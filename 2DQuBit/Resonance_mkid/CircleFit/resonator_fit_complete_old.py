"""
Per runnare:
    python resonator_fit_complete.py --file data.npz
"""

import argparse
import math
import numpy as np
from scipy.optimize import least_squares, curve_fit
import scipy.stats as stats
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

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

def run_pipeline(npz_file, key='0', window_hz=None, show_plots=True):
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

    # ---------------- Estimate and remove cable delay -------------------------
    fitter = CircleEstimator()
    tau_guess = fitter.estimate_delay(freqs, S21)
    print(f"Initial delay guess (tau_guess) = {tau_guess:.6e} s")

    S21_no_delay = fitter.remove_delay(freqs, S21, tau_guess)
    tau_refined = fitter.fit_with_delay(freqs, S21_no_delay)
    print(f"Refined delay (tau_refined) = {tau_refined:.6e} s")

    S21_cal = fitter.remove_delay(freqs, S21_no_delay, tau_refined)

    # ---------------- Circle fit (calibrated data) ----------------------------
    x_c, y_c, r = fitter.fit_from_complex(S21_cal)
    print(f"Circle center: ({x_c:.6e}, {y_c:.6e}), radius = {r:.6e}")
    S21_centered = S21_cal - (x_c + 1j * y_c)
    phase_centered = np.unwrap(np.angle(S21_centered))

    # ---------------- Phase fit to estimate fr and Qr -------------------------
    idx_min = np.argmin(mag)
    fr_guess = freqs[idx_min]
    theta0_guess = phase_centered[0]
    Qr_guess = max(1e3, fr_guess / 1e6)
    p0_phase = [theta0_guess, Qr_guess, fr_guess]

    lower = [-10 * np.pi, 1e1, freqs.min()]
    upper = [10 * np.pi, 1e9, freqs.max()]
    res_phase = least_squares(lambda p: phase_model(freqs, *p) - phase_centered, x0=p0_phase, bounds=(lower, upper))
    theta0_fit, Qr_fit, fr_fit = res_phase.x
    print(f"Phase fit results: fr={fr_fit:.6e} Hz, Qr={Qr_fit:.3f}, theta0={theta0_fit:.3f}")

    # ---------------- Compute canonicalization parameters --------------------
    beta = theta0_fit + math.pi
    P_off = (x_c + r * math.cos(beta)) + 1j * (y_c + r * math.sin(beta))
    amp_scaling = abs(P_off)
    alpha_rot = np.angle(P_off)
    print(f"Canonicalization: amp={amp_scaling:.3e}, alpha={alpha_rot:.3f} rad")
    S21_canon = fitter.canonize_data(freqs, S21_cal, amp_scaling, alpha_rot, 0.0)
    x_can, y_can, r_can = fitter.fit_from_complex(S21_canon)
    print(f"Canonical circle: center=({x_can:.3e},{y_can:.3e}), r={r_can:.3e}")

    # estimate Qc from geometry
    phi0 = -np.arcsin(y_can / r_can)
    Qc_est = Qr_fit / (2.0 * r_can * np.exp(-1j * phi0))
    print(f"Estimates from circle: Qr={Qr_fit:.3f}, |Qc|={abs(Qc_est):.3f}, arg(Qc)={np.angle(Qc_est):.3f}")

    # ---------------- Optionally crop window around resonance ----------------
    if window_hz is not None:
        half = window_hz / 2.0
        mask = (freqs >= fr_fit - half) & (freqs <= fr_fit + half)
        freqs_fit = freqs[mask]
        S21_fit_input = S21[mask]
        print(f"Using window around resonance: {freqs_fit.size} points")
    else:
        freqs_fit = freqs
        S21_fit_input = S21

    ydata = np.concatenate([S21_fit_input.real, S21_fit_input.imag])
    p0_notch = [Qr_fit, abs(Qc_est), np.angle(Qc_est), fr_fit, amp_scaling, alpha_rot, tau_guess + tau_refined]
    lb = [1.0, 1e-2, -np.pi, freqs_fit.min(), 1e-6, -np.pi, -1e-4]
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

        ax_iq = fig.add_subplot(gs[:, 0])
        ax_iq.plot(S21.real, S21.imag, '.', ms=4, label='data')
        ax_iq.plot(S21_fitted_full.real, S21_fitted_full.imag, '-', lw=1, label='notch fit')
        ax_iq.set_title('IQ plane')
        ax_iq.set_xlabel('Re(S21)')
        ax_iq.set_ylabel('Im(S21)')
        ax_iq.legend()
        ax_iq.set_aspect('equal', 'box')

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

        plt.show()

    Qc_fit = abs_Qc_fit * np.exp(1j * phase_Qc_fit)
    Qi_fit = 1.0 / (1.0 / Ql_fit - 1.0 / Qc_fit.real) if not np.isclose(Ql_fit, 0.0) and not np.isclose(Qc_fit.real, 0.0) else np.nan

    return {
        'freqs': freqs,
        'S21': S21,
        'S21_fit': S21_fitted_full,
        'popt': popt,
        'pcov': pcov,
        'residuals': residuals_complex,
        'res_mean': res_mean,
        'res_cov': res_cov,
        'Qc_fit': Qc_fit,
        'Qi_fit': Qi_fit
    }

# ----------------------------- CLI -----------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Resonator fitting pipeline')
    parser.add_argument('--file', '-f', required=True, help='Path to .npz data file')
    parser.add_argument('--key', '-k', default='0', help='Key inside the npz (default: 0)')
    parser.add_argument('--window', '-w', type=float, default=None, help='Optional window width around fr in Hz')
    args = parser.parse_args()

    results = run_pipeline(args.file, key=args.key, window_hz=args.window)
    print('Done. Results returned in dictionary.\n')
