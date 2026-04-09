# This program works perfectly for synthetic data, for some of our resonances it also works decently,
# e.g. with picco6_big. It is not suited for pico_small files because it needs data far from 
# resonance in order to get time delay estimate.
# I will try to work a bit on time delay fit separately and try to understand why in some cases 
# internal quality factor results negative (e.g. in picco2_big)

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

def S21_probst(f, a, alpha, Ql, Qc_mag, phi, fr, tau):
    """Full complex S21 model for a notch resonator (Probst Eq. 1)."""
    Qc = Qc_mag * np.exp(-1j * phi)
    x = 2 * Ql * (f - fr) / fr
    notch = 1 - (Ql / Qc) / (1 + 1j * x)
    env = a * np.exp(1j * alpha) * np.exp(-2j * np.pi * f * tau)
    return env * notch

def fit_wrapper(f, a, alpha, Ql, Qc_mag, phi, fr, tau):
    """Flattens complex array for scipy.optimize.curve_fit."""
    model = S21_probst(f, a, alpha, Ql, Qc_mag, phi, fr, tau)
    return np.concatenate([model.real, model.imag])

# -------------------------------------------------------
# Core Automated Pipeline
# -------------------------------------------------------
def fit_resonance(freq, S21_raw, show_diagnostics=False, show_intermediate_plots=False):
    """
    Executes the full automated Probst fitting routine on raw S21 data.
    """
    # --- Step 1: Automated Cable Delay (tau) ---
    fr_idx = np.argmin(np.abs(S21_raw))
    fr_guess = freq[fr_idx]
    
    span = freq[-1] - freq[0]
    f_left_bound = fr_guess - 0.3 * span
    f_right_bound = fr_guess + 0.3 * span
    
    tail_mask = (freq < f_left_bound) | (freq > f_right_bound)
    phase_raw_unwrapped = np.unwrap(np.angle(S21_raw))
    
    def linear(f, m, b): return -2 * np.pi * m * f + b
    popt_delay, _ = curve_fit(linear, freq[tail_mask], phase_raw_unwrapped[tail_mask])
    tau0 = popt_delay[0]
    phase_intercept = popt_delay[1]
    
    # Remove delay
    S21_no_delay = S21_raw * np.exp(2j * np.pi * freq * tau0)
    phase_nodelay_unwrapped = np.unwrap(np.angle(S21_no_delay))
    
    # --- Step 2: First Circle Fit ---
    xc, yc, r0 = fit_circle_taubin(S21_no_delay.real, S21_no_delay.imag)
    
    # --- Step 3: Shift and Phase Fit (Eq 12) ---
    S21_shifted = S21_no_delay - (xc + 1j * yc)
    theta_shifted = np.unwrap(np.angle(S21_shifted)) 
    
    popt_theta, _ = curve_fit(
        theta_model, freq, theta_shifted, 
        p0=[-np.pi, 1000, fr_guess]
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
    Qi0 = (Qc_mag0 * Ql0) / (Qc_mag0 - Ql0)
    
    # --- Step 5: Global 7-Parameter Fit ---
    p0 = [a0, alpha0, Ql0, Qc_mag0, phi0, fr0, tau0]
    S21_vec = np.concatenate([S21_raw.real, S21_raw.imag])
    
    popt_global, pcov = curve_fit(
        fit_wrapper, freq, S21_vec, p0=p0, maxfev=50000
    )
    
    a_fit, alpha_fit, Ql_fit, Qc_mag_fit, phi_fit, fr_fit, tau_fit = popt_global
    
    # Wrap alphas between 0 and 2*pi
    alpha_fit = alpha_fit % (2 * np.pi)
    alpha0 = alpha0 % (2 * np.pi)
    
    Qi_fit = (Qc_mag_fit * Ql_fit) / (Qc_mag_fit - Ql_fit)
    
    results = {
        "a": a_fit, "a_0": a0,
        "alpha": alpha_fit, "alpha_0": alpha0,
        "tau": tau_fit, "tau_0": tau0,
        "fr": fr_fit, "fr_0": fr0,
        "Ql": Ql_fit, "Ql_0": Ql0,
        "Qc_mag": Qc_mag_fit, "Qc_mag_0": Qc_mag0,
        "Qi": Qi_fit, "Qi_0": Qi0,
        "phi": phi_fit, "phi_0": phi0
    }
    
    # -------------------------------------------------------
    # Intermediate Plots Block
    # -------------------------------------------------------
    if show_intermediate_plots:
        
        # Plot 1: Circles with and without cable delay
        plt.figure(figsize=(6, 6))
        plt.plot(S21_raw.real, S21_raw.imag, '.', ms=2, label="Raw (With Cable Delay)", color='blue', alpha=0.6)
        plt.plot(S21_no_delay.real, S21_no_delay.imag, '.', ms=2, label="Corrected (No Delay)", color='green')
        plt.title("Step 1: Cable Delay Removal (Complex Plane)")
        plt.xlabel("Re(S21)")
        plt.ylabel("Im(S21)")
        plt.grid(True)
        plt.axis("equal")
        plt.legend()
        plt.show()

        # Plot 2: Magnitude and Phase vs Frequency
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        ax1.plot(freq, 20 * np.log10(np.abs(S21_raw)), '.', ms=2, label="Magnitude")
        ax1.set_title("Magnitude vs Frequency")
        ax1.set_xlabel("Frequency (Hz)")
        ax1.set_ylabel("|S21| (dB)")
        ax1.grid(True)
        ax1.legend()

        ax2.plot(freq, phase_raw_unwrapped, '.', ms=2, label="Raw Phase (Unwrapped)", color='blue', alpha=0.6)
        ax2.plot(freq, linear(freq, tau0, phase_intercept), 'r-', lw=2, label="Linear Fit (Tails)")
        ax2.plot(freq, phase_nodelay_unwrapped, '.', ms=2, label="Corrected Phase", color='green')
        
        # Visually delimit the regions used for the tail fit
        ax2.axvspan(freq[0], f_left_bound, color='gray', alpha=0.2, label="Fit Region (Tails)")
        ax2.axvspan(f_right_bound, freq[-1], color='gray', alpha=0.2)
        
        ax2.set_title("Phase vs Frequency (Cable Delay Fit)")
        ax2.set_xlabel("Frequency (Hz)")
        ax2.set_ylabel("Phase (rad)")
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        plt.show()

        # Plot 3: Canonical Circle and Fit
        theta_plot = np.linspace(0, 2*np.pi, 400)
        circle_x = xc_norm + r0_norm * np.cos(theta_plot)
        circle_y = yc_norm + r0_norm * np.sin(theta_plot)

        plt.figure(figsize=(6, 6))
        plt.plot(S21_norm.real, S21_norm.imag, '.', ms=3, label="Normalized S21 Data", color='purple')
        plt.plot(circle_x, circle_y, 'r-', lw=2, label="Algebraic Fit")
        plt.plot(xc_norm, yc_norm, 'ko', label="Circle Center")
        
        plt.plot([xc_norm, xc_norm - r0_norm], [yc_norm, yc_norm], 'k--', label="Radius r₀")
        plt.axhline(0, color='gray', linewidth=1.2)
        plt.axvline(0, color='gray', linewidth=1.2)

        plt.title("Step 4: Canonical Circle Fit (Chernov-Taubin)")
        plt.xlabel("Re(S21)")
        plt.ylabel("Im(S21)")
        plt.grid(True)
        plt.axis("equal")
        plt.legend(loc="upper right")
        plt.show()

    # -------------------------------------------------------
    # Final Diagnostic Plot Block
    # -------------------------------------------------------
    if show_diagnostics:
        S21_fit = S21_probst(freq, *popt_global)
        residuals = np.abs(S21_raw - S21_fit)
        
        plt.figure(figsize=(10, 8))
        plt.subplot(2, 1, 1)
        plt.plot(S21_raw.real, S21_raw.imag, '.', ms=2, label="Raw Data", color='blue')
        plt.plot(S21_fit.real, S21_fit.imag, '-', lw=2, label="Global Fit", color='red')
        plt.title(f"S21 Complex Plane (Fr = {fr_fit/1e9:.4f} GHz, Qi = {Qi_fit:.0f})")
        plt.xlabel("Re(S21)")
        plt.ylabel("Im(S21)")
        plt.grid(True)
        plt.axis("equal")
        plt.legend()
        
        plt.subplot(2, 1, 2)
        plt.plot(freq, residuals, '.k', ms=2)
        plt.title("Fit Residuals |S21_data - S21_fit|")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Error Magnitude")
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()
        
    return results

# -------------------------------------------------------
# Execution Block
# -------------------------------------------------------
if __name__ == "__main__":
    # Load raw synthetic data
    data = pd.read_csv("CRIO_measures/picco6_small.csv")
    #data = pd.read_csv("synthetic_s21.csv")
    #mask = (data["frequency"] >= 7.4810e9)
    #data = data[mask]
    freq_data = data["frequency"].values
    S21_data = data["Re(S21)"].values + 1j * data["Im(S21)"].values
    
    # Run the automated pipeline
    print("Running automated Probst fitting pipeline...")
    final_params = fit_resonance(
        freq_data, 
        S21_data, 
        show_diagnostics=True, 
        show_intermediate_plots=True
    )
    
    # Print clean results with intermediate comparisons
    print("\n===== Final Extracted Parameters =====")
    print(f"Resonance Freq (fr) : {final_params['fr']/1e9:.6f} GHz (first fit {final_params['fr_0']/1e9:.6f} GHz)")
    print(f"Internal Q (Qi)     : {final_params['Qi']:.0f} (first fit {final_params['Qi_0']:.0f})")
    print(f"Coupling Q (|Qc|)   : {final_params['Qc_mag']:.0f} (first fit {final_params['Qc_mag_0']:.0f})")
    print(f"Loaded Q (Ql)       : {final_params['Ql']:.0f} (first fit {final_params['Ql_0']:.0f})")
    print(f"Mismatch Phase (phi): {final_params['phi']:.4f} rad (first fit {final_params['phi_0']:.4f} rad)")
    print(f"Cable Delay (tau)   : {final_params['tau']*1e9:.4f} ns (first fit {final_params['tau_0']*1e9:.4f} ns)")
    print(f"Amplitude Scale (a) : {final_params['a']:.4f} (first fit {final_params['a_0']:.4f})")
    print(f"Global Phase (alpha): {final_params['alpha']:.4f} rad (first fit {final_params['alpha_0']:.4f} rad)")