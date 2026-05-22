import argparse
import math
import numpy as np
from scipy.optimize import least_squares, curve_fit
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from gap_finder_class import GapFinder
import os

from ResonatorFitter import CircleEstimator 

# ----------------------------- Utility helpers -----------------------------

def safe_load_npz(fname, key='0'):
    """Carica un file .npz e ritorna il record associato a `key`."""
    arr = np.load(fname, allow_pickle=True)
    print(f"DEBUG: keys in {fname}: {arr.files}")
    if key not in arr.files:
        key = arr.files[0]
        print(f"WARN: requested key not found, using first key: {key}")

    data = arr[key]

    if isinstance(data, np.ndarray) and data.dtype == object and data.size == 1:
        candidate = data[0]
        if isinstance(candidate, dict):
            return candidate
        if hasattr(candidate, 'dtype') and getattr(candidate.dtype, 'names', None):
            data = candidate

    if hasattr(data, 'dtype') and getattr(data.dtype, 'names', None):
        mapping = {}
        for name in ['freq', 'frequency', 'f', 'frequencies']:
            if name in data.dtype.names:
                mapping['freq'] = name
                break
        for name in ['signal', 's21', 'S21', 'mag']:
            if name in data.dtype.names:
                mapping['signal'] = name
                break
        for name in ['phase', 'arg', 'angle']:
            if name in data.dtype.names:
                mapping['phase'] = name
                break
        if 'freq' in mapping and 'signal' in mapping and 'phase' in mapping:
            return {
                'freq': data[mapping['freq']],
                'signal': data[mapping['signal']],
                'phase': data[mapping['phase']]
            }

    if isinstance(data, dict):
        return data

    if isinstance(data, np.ndarray) and data.ndim == 2 and data.shape[1] >= 3:
        return {'freq': data[:, 0], 'signal': data[:, 1], 'phase': data[:, 2]}

    raise ValueError('Formato .npz non riconosciuto; controlla le chiavi e il contenuto')


def check_nan_inf(*arrays):
    """Ritorna True se uno degli array contiene NaN o Inf (per debug)."""
    for a in arrays:
        a = np.asarray(a)
        if np.isnan(a).any() or np.isinf(a).any():
            return True
    return False

# ----------------------------- Model definitions ----------------------------

def phase_model(freqs, theta0, Qr, fr):
    """Modulo phase model: theta0 + 2*atan(2*Qr*(1 - f/fr))"""
    return theta0 + 2.0 * np.arctan(2.0 * Qr * (1.0 - freqs / fr))

def S21_notch_complex(freqs, Ql, abs_Qc, phase_Qc, fr, amp, alpha, tau):
    """Modello notch canonico complesso."""
    phi = phase_Qc
    prefactor = amp * np.exp(1j * alpha) * np.exp(-1j * 2.0 * np.pi * tau * freqs)
    denom = 1.0 + 2.0j * Ql * (freqs / fr - 1.0)
    coupling = (Ql / abs_Qc) * np.exp(1j * phi)
    return prefactor * (1.0 - coupling / denom)

def S21_notch_real_stacked(freqs, Ql, abs_Qc, phase_Qc, fr, amp, alpha, tau):
    """Funzione di appoggio per curve_fit che concatena real e imag in un vettore reale."""
    z = S21_notch_complex(freqs, Ql, abs_Qc, phase_Qc, fr, amp, alpha, tau)
    return np.concatenate([z.real, z.imag])

# ----------------------------- Main pipeline --------------------------------

def run_pipeline(npz_file, key='0', window_hz=None, show_plots=False, save=False, name=None):
    """Esegue tutto il workflow: caricamento, calibrazione, fits, e plotting."""

    # ---------------- Load data -------------------------------------------------
    raw = safe_load_npz(npz_file, key=key)
    freqs = np.asarray(raw['freq'], dtype=float)
    mag = np.asarray(raw['signal'], dtype=float)
    ph = np.asarray(raw['phase'], dtype=float)
    S21 = mag * np.exp(1j * ph)
    print(f"Loaded {freqs.size} points from {npz_file}")
    

    if check_nan_inf(freqs, mag, ph, S21):
        raise ValueError('I dati contengono NaN o Inf — controlla il file')
    
    fitter = CircleEstimator()
        # 1. Stima grossolana (lineare)
    tau_guess = fitter.estimate_delay(freqs, S21)
    # 2. Raffinamento numerico PARTENDO dai dati originali (S21)
    # Passiamo tau_guess come initial_delay alla funzione leastsq
    tau_final = fitter.fit_with_delay(freqs, S21, initial_delay=tau_guess)
    # 3. Applicazione finale dell'unico delay calcolato
    S21_cal = fitter.remove_delay(freqs, S21, tau_final)

    # ---------------- VNA_probably calibrate already the data -------------------------
    
    x_c, y_c, r = fitter.fit_from_complex(S21_cal)
    print(f"Circle center: ({x_c:.6e}, {y_c:.6e}), radius = {r:.6e}")
    S21_centered = S21_cal - (x_c + 1j * y_c)
    phase_centered = np.unwrap(np.angle(S21_centered))

    # ---------------- Phase fit to estimate fr and Qr -------------------------
    idx_min = np.argmin(mag)
    fr_guess = freqs[idx_min]
    theta0_guess = phase_centered[idx_min]
    Qr_guess = max(1e3, fr_guess / 1e6)
    p0_phase = [theta0_guess, Qr_guess, fr_guess]

    lower = [-10 * np.pi, 1e1, freqs.min()]
    upper = [10 * np.pi, 1e9, freqs.max()]
    res_phase = least_squares(lambda p: phase_model(freqs, *p)-phase_centered, x0=p0_phase, bounds=(lower, upper))
    theta0_fit, Qr_fit, fr_fit = res_phase.x
    print(f"Phase fit results: fr={fr_fit:.6e} Hz, Qr={Qr_fit:.3f}, theta0={theta0_fit:.3f}")

    # ---------------- Compute canonicalization parameters --------------------
    beta = (theta0_fit + math.pi) % (2*math.pi)
    P_off = (x_c + 1j*y_c) + r * np.exp(1j * beta) 
    amp_scaling = abs(P_off)
    alpha_rot = np.angle(P_off)
    print(f"Canonicalization: amp={amp_scaling:.3e}, alpha={alpha_rot:.3f} rad")
    S21_canon = fitter.canonize_data(freqs, S21_cal, amp_scaling, alpha_rot, 0.0)
    x_can, y_can, r_can = fitter.fit_from_complex(S21_canon)
    print(f"Canonical circle: center=({x_can:.3e},{y_can:.3e}), r={r_can:.3e}")


    # estimate Qc from geometry
    phi0 = -np.arcsin(y_can / r_can)
    # 2. Applica la rotazione di asimmetria per raddrizzare il diametro
    # S21_canon_final avrà il diametro perfettamente sull'asse reale

    S21_canon_rect = 1 - (1 - S21_canon) * np.exp(-1j * phi0)

    Qc_est = Qr_fit / (2.0 * r_can * np.exp(-1j * phi0))
  
    print(f"Estimates from circle: Qr={Qr_fit:.3f}, |Qc|={abs(Qc_est):.3f}, arg(Qc)={np.angle(Qc_est):.3f}")

    # ---------------- Optionally crop window around resonance ----------------
    if window_hz is not None:
        half = window_hz / 2.0
        mask = (freqs >= fr_fit - half) & (freqs <= fr_fit + half)
        freqs_fit = freqs[mask]
        S21_fit_input = S21_canon_rect[mask]
        print(f"Using window around resonance: {freqs_fit.size} points")
    else:
        freqs_fit = freqs
        S21_fit_input = S21

    ydata = np.concatenate([S21_fit_input.real, S21_fit_input.imag])
    p0_notch = [Qr_fit, abs(Qc_est), np.angle(Qc_est), fr_fit, amp_scaling, alpha_rot, tau_final]
    lb = [1.0, 1e-5, -np.pi, freqs_fit.min(), 1e-2, -np.pi, -1e-4]
    ub = [1e10, 1e10, np.pi, freqs_fit.max(), 1e2, np.pi, 1e-3]

    try:
        popt, pcov = curve_fit(S21_notch_real_stacked, freqs_fit, ydata, p0=p0_notch, bounds=(lb, ub), maxfev=50000)
    except RuntimeError as e:
        print('curve_fit failed:', e)
        freqs_fit = freqs
        S21_fit_input = S21
        ydata = np.concatenate([S21_fit_input.real, S21_fit_input.imag])
        popt, pcov = curve_fit(S21_notch_real_stacked, freqs_fit, ydata, p0=p0_notch, bounds=(lb, ub), maxfev=50000)

    Ql_fit, abs_Qc_fit, phase_Qc_fit, fr_fit2, amp_fit, alpha_fit, tau_fit = popt
    print('\nNotch fit results:')
    print(f" Ql = {Ql_fit:.3f}")
    print(f" |Qc| = {abs_Qc_fit:.3f}, phase(Qc) = {phase_Qc_fit:.3f} rad")
    print(f" fr = {fr_fit2:.6e} Hz")
    print(f" amp = {amp_fit:.3e}, alpha = {alpha_fit:.3f} rad, tau = {tau_fit:.3e} s")

    S21_fitted_full = S21_notch_complex(freqs, Ql_fit, abs_Qc_fit, phase_Qc_fit, fr_fit2, amp_fit, alpha_fit, tau_fit)
    residuals_complex = S21 - S21_fitted_full
    res_mag = np.abs(residuals_complex)
    res_phase = np.unwrap(np.angle(S21)) - np.unwrap(np.angle(S21_fitted_full))

    res_mean = np.mean(residuals_complex)
    res_cov = np.cov(np.column_stack([residuals_complex.real, residuals_complex.imag]).T)
    print('\nResiduals summary:')
    print(f' mean (Re,Im) = ({res_mean.real:.3e},{res_mean.imag:.3e})')
    print(' covariance matrix (Re,Im):')
    print(res_cov)

    sw_real = stats.shapiro(residuals_complex.real) if residuals_complex.size <= 5000 else (np.nan, np.nan)
    sw_imag = stats.shapiro(residuals_complex.imag) if residuals_complex.size <= 5000 else (np.nan, np.nan)
    print(f"Shapiro real: {sw_real}, Shapiro imag: {sw_imag}")

    if show_plots:
        fig = plt.figure(figsize=(14, 9))
        gs = GridSpec(3, 3, figure=fig, width_ratios=[2, 1, 1], height_ratios=[1, 1, 1], hspace=0.4, wspace=0.3)

        ax_iq = fig.add_subplot(gs[1:3, 0])
        ax_iq.plot(S21.real, S21.imag, '.', ms=4, label='data')
        ax_iq.plot(S21_fitted_full.real, S21_fitted_full.imag, '-', lw=1, label='notch fit')
        ax_iq.set_title(f'IQ plane {name}')
        ax_iq.set_xlabel('Re(S21)')
        ax_iq.set_ylabel('Im(S21)')
        ax_iq.grid(True)
        ax_iq.legend()
        ax_iq.set_aspect('equal', 'box')

        ax_rect = fig.add_subplot(gs[0, 0])
        ax_rect.plot(S21_canon_rect.real, S21_canon_rect.imag, '.', ms=4, label='rectified data')
        ax_rect.set_title('Rectified IQ data')
        ax_rect.set_xlabel('Re(S21)')
        ax_rect.set_ylabel('Im(S21)')
        ax_rect.grid(True)
        ax_rect.legend()
        ax_rect.set_aspect('equal', 'box')

        ax_mag = fig.add_subplot(gs[0, 1])
        ax_mag.plot(freqs / 1e9, np.abs(S21), '.', ms=3, label='data')
        ax_mag.plot(freqs / 1e9, np.abs(S21_fitted_full), '-', lw=1, label='fit')
        ax_mag.set_title('Magnitude vs frequency')
        ax_mag.set_xlabel('f [GHz]')
        ax_mag.set_ylabel('|S21|')
        ax_mag.legend()
        ax_mag.grid(True)

        ax_phase = fig.add_subplot(gs[0, 2])
        ax_phase.plot(freqs / 1e9, np.unwrap(np.angle(S21)), '.', ms=3, label='data')
        ax_phase.plot(freqs / 1e9, np.unwrap(np.angle(S21_fitted_full)), '-', lw=1, label='fit')
        ax_phase.set_title('Phase vs frequency')
        ax_phase.set_xlabel('f [GHz]')
        ax_phase.set_ylabel('phase [rad]')
        ax_phase.legend()
        ax_phase.grid(True)

        ax_hist = fig.add_subplot(gs[1, 1])
        ax_hist.hist(res_mag, bins=60)
        ax_hist.set_title('Residual magnitude histogram')
        ax_hist.set_xlabel('|res|')

        ax_qq = fig.add_subplot(gs[1, 2])
        stats.probplot(residuals_complex.real, dist='norm', plot=ax_qq)
        ax_qq.set_title('QQ plot (Re residuals)')

        ax_resf = fig.add_subplot(gs[2, 1:3])
        ax_resf.plot(freqs / 1e9, res_mag, '.', ms=3)
        ax_resf.set_xlabel('f [GHz]')
        ax_resf.set_ylabel('|res|')
        ax_resf.set_title('Residual magnitude vs frequency')
        ax_resf.grid(True)
        if save == True:
            plt.savefig(f"{npz_file}_fit_results.png", dpi=300)
        #plt.show()
    
    inv_Qc_complex = 1.0 / (abs_Qc_fit * np.exp(1j * phase_Qc_fit))
    inv_Qi = (1.0 / Ql_fit) - inv_Qc_complex.real
    Qi_fit_final = 1.0 / inv_Qi if inv_Qi > 0 else np.nan
    Qc_fit_final = abs_Qc_fit * np.exp(1j * phase_Qc_fit)

    
    return {
        'freqs': freqs,
        'S21': S21,
        'S21_fit': S21_fitted_full,
        'popt': popt,
        'pcov': pcov,
        'residuals': residuals_complex,
        'res_mean': res_mean,
        'res_cov': res_cov,
        'Qc_fit': Qc_fit_final,
        'Qi_fit': Qi_fit_final,
        'Ql_fit': Ql_fit,
        'fr_fit': fr_fit2
    }

def calcola_gap_superconduttivo(Temperature, Q_internal, err_inv_Qi, f_risonanza, T_limit=260, fit_type='kondo'):
    """
    Usa i dati estratti da main_fit.py per calcolare l'energia di gap con GapFinder.
    """
    print(f"\n--- Avvio Fit Gap ({fit_type.upper()}) ---")
    
    # 1. Calcoliamo 1/Qi dai Q_internal estratti
    Temperature = np.array(Temperature)
    inv_Qi = 1.0 / np.array(Q_internal)
    err_inv_Qi = np.array(err_inv_Qi)
    
    # 2. Creiamo il file temporaneo richiesto da GapFinder
    data_to_save = np.column_stack([Temperature, inv_Qi, err_inv_Qi])
    filename = "qi_vs_t_temp.txt"
    np.savetxt(filename, data_to_save, fmt=['%d', '%.6E', '%.6E'])
    
    # Usiamo la media delle frequenze di risonanza come f0 (omega)
    omega0 = np.mean(f_risonanza) 
    
    # 3. Inizializziamo GapFinder
    gap_obj = GapFinder(filename, omega=omega0, fit_type=fit_type)
    gap_obj.set_T_limit(T_limit)
    
    # 4. Eseguiamo il fit e plottiamo
    # (Nella classe GapFinder, plot_fit() chiama internamente il fit)
    gap_obj.plot_fit()
    
    # 5. Estraiamo i risultati
    delta0_scaled = gap_obj.fit_result.values[0]
    deltaErr_scaled = gap_obj.fit_result.errors[0]
    
    delta0 = delta0_scaled * 1e-23
    deltaErr = deltaErr_scaled * 1e-23
    
    k_B = 1.38e-23 # Costante di Boltzmann
    tc = delta0 * (2 / 3.52) / k_B
    tcErr = deltaErr * (2 / 3.52) / k_B
    chi2 = round(gap_obj.chi2(), 3)
    
    # 6. Stampiamo a schermo in modo leggibile
    print(f"\n--- Risultati Fit Gap ---")
    print(f"Tc     = {tc*1000:.2f} ± {tcErr*1000:.2f} mK")
    print(f"Delta0 = {delta0*6.242e+18:.3e} ± {deltaErr*6.242e+18:.3e} eV")
    print(f"Chi2   = {chi2}")
    
    FitResult = {
        'Tc_K': tc, 'TcErr_K': tcErr, 
        'Delta0_J': delta0*6.242e+18, 'Delta0Err_J': deltaErr*6.242e+18, 
        'chi2': chi2
    }
    
    if fit_type == 'kondo':
        FitResult['TK'] = gap_obj.fit_result.values[1]
        FitResult['TKErr'] = gap_obj.fit_result.errors[1]
        print(f"T_K    = {FitResult['TK']:.2f} ± {FitResult['TKErr']:.2f} mK")
        
    return FitResult

# ----------------------------- CLI -----------------------------------------

if __name__ == '__main__':
    # Sostituiamo il parser con valori fissi per bypassare il terminal
    # Solo per scopi dimostrativi, rimuovi questo loop se vuoi usare argparse normalmente
    list_freqs = []
    list_S21 = []
    list_fresonance = []
    Q_loaded = []
    Q_internal = []
    Q_internal_inverted = []
    Q_coupling = []
    Temperature = [ 200, 300, 400, 500, 600, 700]#, 750]#, 820]#, 850]#, 900, 950, 1000, 1050] # mK
    H = 1

    for i in Temperature:
        if i == 900:
            file = f"{H}peak_{i}mK_3000pt.npz"
        if i == 950 or i == 1000:
            file = f"{H}peak_{i}mK_2000pt.npz"
        if i == 1050: 
            file = f"{H}peak_{i}mK_1000pt.npz"
        else:
            file = f"{H}peak_{i}mK.npz"
        
        file_da_analizzare = f"C:/Users/oper/labQT/Lab2025/2DQubit_organizzato/Data/Resonator/1st_peak_resonance/" + file  # Assicurati che il nome sia esatto
        chiave_dati = "0"      # Di solito è '0'
        finestra_hz = None                     # Puoi mettere un numero se serve (es. 1000000)

        print(f"--- Avvio analisi su: {file_da_analizzare} ---")
        
        # Lanciamo la pipeline direttamente
        try:
            results = run_pipeline(file_da_analizzare, key=chiave_dati, window_hz=finestra_hz, save = False, show_plots=False, name = file)
            print("Analisi completata con successo!")
            list_freqs.append(results['freqs'])
            list_S21.append(results['S21_fit'])
            list_fresonance.append(results['fr_fit'])
            Q_loaded.append(results['Ql_fit'])
            Q_internal.append(results['Qi_fit'])
            Q_internal_inverted.append(1.0 / results['Qi_fit'] if results['Qi_fit'] != 0 else np.nan)
            Q_coupling.append(abs(results['Qc_fit']))
        except Exception as e:
            print(f"Errore durante l'esecuzione: {e}")
        
        file = None  # Reset per sicurezza

Temperature = np.array(Temperature)
inv_Qi_values = np.array(Q_internal_inverted)
errore_stimato_inv_Qi = inv_Qi_values * 0.05 

risultati_gap = calcola_gap_superconduttivo(
    Temperature=Temperature, 
    Q_internal=Q_internal, 
    err_inv_Qi=errore_stimato_inv_Qi, # Passiamo gli errori
    f_risonanza=list_fresonance,      # Serve per calcolare omega0
    T_limit=1200,                      # Temperatura limite
    fit_type='standard'                  # 'kondo' o 'bcs'
)