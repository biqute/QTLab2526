import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# -------------------------------------------------------
# Mathematical Models & Helpers
# -------------------------------------------------------
def fit_circle_taubin(x, y):
    """Chernov-Taubin algebraic circle fit."""
    x_m, y_m = np.mean(x), np.mean(y)
    u, v = x - x_m, y - y_m
    
    Suu, Suv, Svv = np.sum(u**2), np.sum(u * v), np.sum(v**2)
    Suuu, Suvv = np.sum(u**3), np.sum(u * v**2)
    Svvv, Svuu = np.sum(v**3), np.sum(v * u**2)
    
    A = np.array([[Suu, Suv], [Suv, Svv]])
    B = 0.5 * np.array([Suuu + Suvv, Svvv + Svuu])
    uc, vc = np.linalg.solve(A, B)
    
    xc, yc = uc + x_m, vc + y_m
    r0 = np.sqrt(uc**2 + vc**2 + (Suu + Svv) / len(x))
    return xc, yc, r0

def theta_model(f, theta0, Ql, fr):
    """Phase angle model (Probst Eq. 12)."""
    return theta0 + 2 * np.arctan(2 * Ql * (1 - f / fr))

def S21_probst_Qi(f, a, alpha, Qi, Qc_mag, phi, fr, tau):
    """
    Modello S21 riscritto per fittare direttamente Qi e forzarne la positività.
    Usa l'Eq. 2 di Probst: 1/Ql = 1/Qi + cos(phi)/|Qc|
    """
    # Deriviamo Ql dinamicamente in modo che rispetti sempre la fisica
    Ql = 1.0 / (1.0 / Qi + np.cos(phi) / Qc_mag)
    
    Qc = Qc_mag * np.exp(-1j * phi)
    x = 2 * Ql * (f - fr) / fr
    notch = 1 - (Ql / Qc) / (1 + 1j * x)
    env = a * np.exp(1j * alpha) * np.exp(-2j * np.pi * f * tau)
    return env * notch

def fit_wrapper_Qi(f, a, alpha, Qi, Qc_mag, phi, fr, tau):
    """Flattens complex array for scipy.optimize.curve_fit."""
    model = S21_probst_Qi(f, a, alpha, Qi, Qc_mag, phi, fr, tau)
    return np.concatenate([model.real, model.imag])

# -------------------------------------------------------
# Core Automated Pipeline
# -------------------------------------------------------
def fit_resonance(freq, S21_raw, fixed_tau=None, show_diagnostics=False):
    fr_idx = np.argmin(np.abs(S21_raw))
    fr_guess = freq[fr_idx]
    span = freq[-1] - freq[0]
    
    # --- Step 1: Cable Delay (tau) ---
    if fixed_tau is not None:
        tau0 = fixed_tau
    else:
        f_left_bound = fr_guess - 0.3 * span
        f_right_bound = fr_guess + 0.3 * span
        tail_mask = (freq < f_left_bound) | (freq > f_right_bound)
        
        if np.sum(tail_mask) < 10:
            f_left_bound = fr_guess - 0.1 * span
            f_right_bound = fr_guess + 0.1 * span
            tail_mask = (freq < f_left_bound) | (freq > f_right_bound)
            if np.sum(tail_mask) < 5:
                tail_mask = np.ones_like(freq, dtype=bool)

        phase_raw_unwrapped = np.unwrap(np.angle(S21_raw))
        def linear(f, m, b): return -2 * np.pi * m * f + b
        popt_delay, _ = curve_fit(linear, freq[tail_mask], phase_raw_unwrapped[tail_mask])
        tau0 = popt_delay[0]

    S21_no_delay = S21_raw * np.exp(2j * np.pi * freq * tau0)
    
    # --- Step 2: First Circle Fit ---
    xc, yc, r0 = fit_circle_taubin(S21_no_delay.real, S21_no_delay.imag)
    
    # --- Step 3: Shift and Phase Fit (Eq 12) ---
    S21_shifted = S21_no_delay - (xc + 1j * yc)
    theta_shifted = np.unwrap(np.angle(S21_shifted)) 
    
    popt_theta, _ = curve_fit(
        theta_model, freq, theta_shifted, 
        p0=[-np.pi, 10000, fr_guess]
    )
    theta0_fit, Ql0, fr0 = popt_theta
    
    beta = theta0_fit + np.pi
    P = xc + r0 * np.cos(beta) + 1j * (yc + r0 * np.sin(beta))
    a0 = np.abs(P)
    alpha0 = np.angle(P)
    
    # --- Step 4: Normalized Circle Fit (phi) ---
    S21_norm = S21_no_delay / (a0 * np.exp(1j * alpha0))
    xc_norm, yc_norm, r0_norm = fit_circle_taubin(S21_norm.real, S21_norm.imag)
    
    phi0 = -np.arcsin(yc_norm / r0_norm)
    Qc_mag0 = Ql0 / (2 * r0_norm)
    if Qc_mag0 == Ql0:
        Qc_mag0 += 1e-5
        
    # Calcolo corretto di Qi0 inclusivo del cos(phi) per il guess iniziale
    inv_Qi0 = 1.0 / Ql0 - np.cos(phi0) / Qc_mag0
    if inv_Qi0 <= 0:
        Qi0 = 1e5  # Fallback di sicurezza se i dati grezzi sembrano non fisici
    else:
        Qi0 = 1.0 / inv_Qi0
    
    # --- Step 5: Global 7-Parameter Fit (ORA CERCA Qi DIRETTAMENTE) ---
    p0 = [a0, alpha0, Qi0, Qc_mag0, phi0, fr0, tau0]
    S21_vec = np.concatenate([S21_raw.real, S21_raw.imag])
    
    # Se hai passato il delay dal VNA, cerca tra +/- 10 ns
    tau_tolerance = 10e-9
    tau_bound_lower = tau0 - tau_tolerance if fixed_tau is not None else -np.inf
    tau_bound_upper = tau0 + tau_tolerance if fixed_tau is not None else np.inf

    # BOUNDS: Il terzo parametro è il Qi. Lo blocchiamo a un minimo di 10.
    # [a, alpha, Qi, Qc_mag, phi, fr, tau]
    bounds_lower = [0, -np.inf, 10, 10, -np.pi, freq[0]*0.8, tau_bound_lower]
    bounds_upper = [np.inf, np.inf, 1e8, 1e8, np.pi, freq[-1]*1.2, tau_bound_upper]
    
    try:
        popt_global, pcov = curve_fit(
            fit_wrapper_Qi, freq, S21_vec, 
            p0=p0, bounds=(bounds_lower, bounds_upper), maxfev=100000
        )
        perr = np.sqrt(np.diag(pcov))
    except RuntimeError:
        print("Errore: il fit globale non è converguto.")
        popt_global = p0
        perr = np.zeros(len(p0))

    a_fit, alpha_fit, Qi_fit, Qc_mag_fit, phi_fit, fr_fit, tau_fit = popt_global
    a_err, alpha_err, Qi_err, Qc_mag_err, phi_err, fr_err, tau_err = perr
    
    alpha_fit = alpha_fit % (2 * np.pi)
    
    # Ricalcoliamo il Ql per mostrarlo nei risultati
    Ql_fit = 1.0 / (1.0 / Qi_fit + np.cos(phi_fit) / Qc_mag_fit)
    
    results = {
        "a": (a_fit, a_err), "alpha": (alpha_fit, alpha_err),
        "tau": (tau_fit, tau_err), "fr": (fr_fit, fr_err),
        "Ql": (Ql_fit, 0), "Qc_mag": (Qc_mag_fit, Qc_mag_err),
        "Qi": (Qi_fit, Qi_err), "phi": (phi_fit, phi_err)
    }
    
    if show_diagnostics:
        S21_fit = S21_probst_Qi(freq, *popt_global)
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(S21_raw.real, S21_raw.imag, '.', label="Dati Raw")
        plt.plot(S21_fit.real, S21_fit.imag, 'r-', label="Fit Globale")
        plt.title(f"Piano Complesso S21\nQi = {Qi_fit:.0f}")
        plt.xlabel("Re(S21)"); plt.ylabel("Im(S21)")
        plt.axis("equal"); plt.grid(True); plt.legend()
        
        plt.subplot(1, 2, 2)
        plt.plot(freq/1e9, 20*np.log10(np.abs(S21_raw)), '.', label="Dati")
        plt.plot(freq/1e9, 20*np.log10(np.abs(S21_fit)), 'r-', label="Fit")
        plt.title("Ampiezza (dB)")
        plt.xlabel("Frequenza (GHz)"); plt.ylabel("|S21| (dB)")
        plt.grid(True); plt.legend()
        
        plt.tight_layout()
        plt.show()
        
    return results

# -------------------------------------------------------
# Execution Block
# -------------------------------------------------------
if __name__ == "__main__":
    file_path = "850mk/picco5_big_new850mk.csv" # Metti qui il tuo file
    
    data = pd.read_csv(file_path)
    freq_data = data["frequency"].values
    S21_data = data["Re(S21)"].values + 1j * data["Im(S21)"].values
    
    # Mettiamo i 100ns letti dal VNA
    delay_vna = 58.3e-9  
    
    final_params = fit_resonance(
        freq_data, S21_data, 
        fixed_tau=delay_vna, 
        show_diagnostics=False
    )
    
print("\n===== Risultati Finali (Qi FORZATO POSITIVO) =====")

fr, fr_err = final_params['fr']
Qi, Qi_err = final_params['Qi']
Qc, Qc_err = final_params['Qc_mag']
Ql, _ = final_params['Ql']
phi, phi_err = final_params['phi']
tau, tau_err = final_params['tau']

print(f"Frequenza (fr)   : {fr:.0f} ± {fr_err} Hz")
print(f"Internal Q (Qi)  : {Qi:.5f} ± {Qi_err:.5f}")
print(f"Coupling Q (Qc)  : {Qc:.0f} ± {Qc_err:.0f}")
print(f"Loaded Q (Ql)    : {Ql:.0f}")
print(f"Mismatch (phi)   : {phi:.4f} ± {phi_err:.4f} rad")
print(f"Cable delay      : {tau*1e9:.4f} ± {tau_err*1e9:.4f} ns")