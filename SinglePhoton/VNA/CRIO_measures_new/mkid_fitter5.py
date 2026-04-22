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
def fit_resonance(freq, S21_raw, show_diagnostics=False, show_intermediate_plots=False, provided_tau=None):
    """
    Executes the full automated Probst fitting routine on raw S21 data.
    If provided_tau is given, it skips the automated tail-fitting in Step 1.
    """
    # --- Step 1: Automated Cable Delay (tau) ---
    fr_idx = np.argmin(np.abs(S21_raw))
    fr_guess = freq[fr_idx]
    
    phase_raw_unwrapped = np.unwrap(np.angle(S21_raw))
    def linear(f, m, b): return -2 * np.pi * m * f + b

    if provided_tau is None:
        # Standard approach: Estimate tau from off-resonance tails
        span = freq[-1] - freq[0]
        f_left_bound = fr_guess - 0.3 * span
        f_right_bound = fr_guess + 0.3 * span
        
        tail_mask = (freq < f_left_bound) | (freq > f_right_bound)
        
        popt_delay, _ = curve_fit(linear, freq[tail_mask], phase_raw_unwrapped[tail_mask])
        tau0 = popt_delay[0]
        phase_intercept = popt_delay[1]
    else:
        # Modified approach: Use provided tau (from "big" file)
        tau0 = provided_tau
        phase_intercept = 0 # Dummy value since we skipped the fit
        f_left_bound, f_right_bound = freq[0], freq[-1] # Dummy bounds for plotting
    
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
    
    # Note: tau is still passed as a parameter to the global fit here. 
    # If the "small" file fit struggles to keep tau stable, you can remove tau from p0 
    # and fit a 6-parameter model here instead.
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
        S21_no_delay_final = S21_raw * np.exp(2j * np.pi * freq * tau_fit)

        # FIGURE 1: 2x2 Circle Evolution
        fig1, axs = plt.subplots(2, 2, figsize=(7, 7))
        
        axs[0, 0].plot(S21_raw.real, S21_raw.imag, '.', ms=2, label="Raw (With Delay)", color='blue', alpha=0.3)
        axs[0, 0].plot(S21_no_delay.real, S21_no_delay.imag, '.', ms=2, label="Corrected (Initial τ₀)", color='green', alpha=0.5)
        axs[0, 0].plot(S21_no_delay_final.real, S21_no_delay_final.imag, '.', ms=2, label="Corrected (Final τ)", color='red', alpha=0.8)
        axs[0, 0].set_title("1. Cable Delay Removal")
        axs[0, 0].grid(True); axs[0, 0].axis("equal"); axs[0, 0].legend()

        P_shifted = P - (xc + 1j * yc)
        axs[0, 1].plot(S21_shifted.real, S21_shifted.imag, '.', ms=2, label="Shifted S21", color='dodgerblue')
        axs[0, 1].plot(P_shifted.real, P_shifted.imag, 'r*', ms=10, label="Point P")
        axs[0, 1].set_title("2. Shifted Circle & Point P")
        axs[0, 1].grid(True); axs[0, 1].axis("equal"); axs[0, 1].legend()

        axs[1, 0].plot(S21_norm.real, S21_norm.imag, '.', ms=3, label="Normalized", color='purple')
        axs[1, 0].set_title("3. S21 Normalized")
        axs[1, 0].grid(True); axs[1, 0].axis("equal"); axs[1, 0].legend()

        theta_plot = np.linspace(0, 2*np.pi, 400)
        circle_x = xc_norm + r0_norm * np.cos(theta_plot)
        circle_y = yc_norm + r0_norm * np.sin(theta_plot)
        axs[1, 1].plot(S21_norm.real, S21_norm.imag, '.', ms=3, label="Data", color='purple', alpha=0.5)
        axs[1, 1].plot(circle_x, circle_y, 'r-', lw=2, label="Fit")
        axs[1, 1].set_title("4. Canonical Circle Fit")
        axs[1, 1].grid(True); axs[1, 1].axis("equal"); axs[1, 1].legend(loc="upper right")
        plt.tight_layout(); plt.show()

        # FIGURE 2: Phase vs Frequency (Delay removal check)
        fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        ax1.plot(freq, 20 * np.log10(np.abs(S21_raw)), '.', ms=2, label="Magnitude")
        ax1.set_title("Magnitude vs Frequency"); ax1.grid(True); ax1.legend()

        ax2.plot(freq, phase_raw_unwrapped, '.', ms=2, label="Raw Phase", color='blue', alpha=0.6)
        if provided_tau is None:
            ax2.plot(freq, linear(freq, tau0, phase_intercept), 'r-', lw=2, label="Linear Fit (Tails)")
            ax2.axvspan(freq[0], f_left_bound, color='gray', alpha=0.2, label="Fit Region")
            ax2.axvspan(f_right_bound, freq[-1], color='gray', alpha=0.2)
        ax2.plot(freq, phase_nodelay_unwrapped, '.', ms=2, label="Corrected Phase", color='green')
        ax2.set_title("Phase vs Frequency"); ax2.grid(True); ax2.legend()
        plt.tight_layout(); plt.show()
        
        # FIGURE 3 & 4 Omitted for brevity in this output, but can remain in your actual code exactly as they were.
        # =================================================================
        theta_fit_curve = theta_model(freq, *popt_theta)

        plt.figure(figsize=(8, 6))
        plt.plot(freq, theta_shifted, '.', ms=3, label="Shifted phase data", color='tab:blue')
        plt.plot(freq, theta_fit_curve, 'r-', lw=2, label="Fit: Probst Eq. (12)")
        
        plt.title("Step 3: Phase Fit to Probst Eq. (12)")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Phase θ (rad)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
        # FIGURE 5: 3-Circle Transformation Progression
        # =================================================================
        # Ensure S21_norm_final is calculated if it isn't already in your code:
        S21_norm_final = S21_no_delay_final / ( np.exp(1j * alpha_fit))  # a_fit *

        plt.figure(figsize=(8, 8))
        
        # 1. Raw Data
        plt.plot(S21_raw.real, S21_raw.imag, '.', ms=2, color='gray', alpha=0.6, label="1. Raw S21")
        
        # 2. Cable Delay Removed
        plt.plot(S21_no_delay_final.real, S21_no_delay_final.imag, '.', ms=2, color='dodgerblue', alpha=0.8, label="2. Delay Removed (τ_fit)")
        
        # 3. Normalized (Delay, Scale, and Phase removed)
        plt.plot(S21_norm_final.real, S21_norm_final.imag, '.', ms=3, color='crimson', label="3. Normalized (a_fit, α_fit removed)")
        
        # Origin lines for reference
        plt.axhline(0, color='black', linewidth=0.8, alpha=0.5)
        plt.axvline(0, color='black', linewidth=0.8, alpha=0.5)
        
        plt.title("S21 Transformation Progression")
        plt.xlabel("Re(S21)")
        plt.ylabel("Im(S21)")
        plt.grid(True)
        plt.axis("equal")  # Crucial so circles aren't stretched into ellipses
        plt.legend(loc="best")
        plt.tight_layout()
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
        plt.grid(True); plt.axis("equal"); plt.legend()
        
        plt.subplot(2, 1, 2)
        plt.plot(freq, residuals, '.k', ms=2)
        plt.title("Fit Residuals |S21_data - S21_fit|")
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        
    return results

# -------------------------------------------------------
# Execution Block
# -------------------------------------------------------
if __name__ == "__main__":
    
    # ---------------------------------------------------
    # PART A: Run fit on the "BIG" file to extract tau
    # ---------------------------------------------------
    print("=== Processing BIG file to extract delay (tau) ===")
    data_big = pd.read_csv("10mk/picco2_big_new10mk.csv")  # Replace with actual big file name
    mask = (data_big["frequency"] >= 7.40e9)
    data_big = data_big[mask]
    freq_big = data_big["frequency"].values
    S21_big = data_big["Re(S21)"].values + 1j * data_big["Im(S21)"].values
    
    params_big = fit_resonance(
        freq_big, 
        S21_big, 
        show_diagnostics=False,       # Turn to True if you want plots for the big file
        show_intermediate_plots=False,
        provided_tau=None             # None means it WILL calculate tau from the tails
    )
    
    extracted_tau = params_big['tau']
    print(f"Extracted tau from big file global fit: {extracted_tau*1e9:.4f} ns")


    # ---------------------------------------------------
    # PART B: Run fit on the "SMALL" file using extracted tau
    # ---------------------------------------------------
    print("\n=== Processing SMALL file using fixed tau ===")
    data_small = pd.read_csv("10mk/picco2_big_new10mk.csv") # Replace with actual small file name
    mask = (data_small["frequency"] >= 7.40e9)
    data_small = data_big[mask]
    freq_small = data_small["frequency"].values
    S21_small = data_small["Re(S21)"].values + 1j * data_small["Im(S21)"].values
    
    params_small = fit_resonance(
        freq_small, 
        S21_small, 
        show_diagnostics=True, 
        show_intermediate_plots=True,
        provided_tau=extracted_tau    # Pass the tau extracted from the big file
    )
    
    # Print clean results for the small file
    print("\n===== Final Extracted Parameters (Small File) =====")
    print(f"Resonance Freq (fr) : {params_small['fr']/1e9:.6f} GHz (first fit {params_big['fr']/1e9:.6f} GHz)")
    print(f"Internal Q (Qi)     : {params_small['Qi']:.0f} (first fit {params_big['Qi']:.0f})")
    print(f"Coupling Q (|Qc|)   : {params_small['Qc_mag']:.0f} (first fit {params_big['Qc_mag']:.0f})")
    print(f"Loaded Q (Ql)       : {params_small['Ql']:.0f} (first fit {params_big['Ql_0']:.0f})")
    print(f"Mismatch Phase (phi): {params_small['phi']:.4f} rad (first fit {params_big['phi']:.4f} rad)")
    print(f"Cable Delay (tau)   : {params_small['tau']*1e9:.4f} ns (Initial input: {params_big['tau']*1e9:.4f} ns)")
    print(f"Amplitude Scale (a) : {params_small['a']:.4f} (first fit {params_big['a_0']:.4f})")
    print(f"Global Phase (alpha): {params_small['alpha']:.4f} rad (first fit {params_big['alpha']:.4f} rad)")