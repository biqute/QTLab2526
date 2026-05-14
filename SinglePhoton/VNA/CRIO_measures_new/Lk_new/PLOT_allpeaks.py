import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# 1. Input Parameters and Targets
target_freqs = {'P1': 7.49, 'P3': 7.99, 'P4': 8.40, 'P5': 8.64}
f_err = 0.01  
X_MIN, X_MAX = 12.5, 16.125 

# Global Font Configuration
plt.rcParams.update({'font.size': 16}) 

def model(Lk, A, Lg):
    """Physical model: f = A / sqrt(Lk + Lg)"""
    return A / np.sqrt(Lk + Lg)

def plot_and_fit_peaks(file_path):
    try:
        df = pd.read_csv(file_path, skipinitialspace=True)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = df.columns.str.strip()
    peaks = ['P1', 'P3', 'P4', 'P5']
    df[peaks] = df[peaks].replace(0, np.nan)

    plt.figure(figsize=(16, 10))
    colors = plt.cm.tab10(np.linspace(0, 1, len(peaks)))
    
    lk_extrapolated_values = []

    for i, peak in enumerate(peaks):
        valid_data = df[['Lk', peak]].dropna()
        x_data, y_data = valid_data['Lk'].values, valid_data[peak].values
        
        if len(x_data) < 2: continue

        try:
            popt, pcov = curve_fit(model, x_data, y_data, p0=[30, 5])
            A_f, Lg_f = popt
            dA, dLg = np.sqrt(np.diag(pcov)) 

            f_t = target_freqs[peak]
            lk_t = (A_f / f_t)**2 - Lg_f
            
            # Error propagation
            term_A = (2 * A_f / f_t**2) * dA
            term_f = (-2 * A_f**2 / f_t**3) * f_err
            term_Lg = dLg
            lk_err_prop = np.sqrt(term_A**2 + term_f**2 + term_Lg**2)
            
            lk_extrapolated_values.append(lk_t)

            # --- Plotting ---
            x_fit = np.linspace(X_MIN, X_MAX, 200)
            plt.plot(x_fit, model(x_fit, *popt), color=colors[i], linestyle='-', alpha=0.3, linewidth=2.5)
            
            # Experimental data (no label for legend)
            plt.errorbar(x_data, y_data, yerr=f_err, fmt='o', color=colors[i], 
                         markersize=7, capsize=5, alpha=0.5)

            # Projections
            plt.plot([X_MIN, lk_t], [f_t, f_t], color=colors[i], linestyle='--', linewidth=1.2, alpha=0.6)
            plt.plot([lk_t, lk_t], [7.0, f_t], color=colors[i], linestyle='--', linewidth=1.2, alpha=0.6)

            # Target frequency labels
            plt.text(X_MIN + 0.1, f_t + 0.015, f'{f_t} GHz', color=colors[i], 
                     va='bottom', ha='left', fontsize=14, fontweight='bold',
                     bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

            # Target Star
            plt.errorbar(lk_t, f_t, yerr=f_err, xerr=lk_err_prop, fmt='*', color='green', 
                         markersize=16, capsize=6, zorder=10)

        except Exception as e: print(f"Error {peak}: {e}")

    # --- Mean Calculation and Confidence Regions ---
    if lk_extrapolated_values:
        mean_lk = np.mean(lk_extrapolated_values)
        std_lk = np.std(lk_extrapolated_values)
        
        # Uncertainty regions
        plt.axvspan(mean_lk - 2*std_lk, mean_lk + 2*std_lk, color='lightblue', alpha=0.2, 
                    label=r'2$\sigma$ Uncertainty ($\pm$' + f'{2*std_lk:.2f})')
        
        plt.axvspan(mean_lk - std_lk, mean_lk + std_lk, color='lightgreen', alpha=0.3, 
                    label=r'1$\sigma$ Uncertainty ($\pm$' + f'{std_lk:.2f})')
        
        # Mean vertical line
        plt.axvline(x=mean_lk, color='black', linestyle='--', linewidth=3.5, zorder=11,
                    label=f'Mean $L_k = {mean_lk:.2f}$')

        # MEAN LK TEXT INSIDE THE PLOT
        plt.text(mean_lk + 0.05, 8.8, f'Mean $L_k$ = {mean_lk:.2f} $\pm$ {std_lk:.2f}', 
                 color='black', fontweight='bold', fontsize=18, zorder=12,
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.3'))

    # --- Final Formatting ---
    plt.title(r'$L_k$ Extrapolation', fontsize=22, pad=25)
    plt.xlabel(r'$L_k$', fontsize=20)
    plt.ylabel(r'$f_0$ (GHz)', fontsize=20)
    
    plt.xlim(X_MIN, X_MAX)
    plt.ylim(7.34, 8.85) 
    
    # Legend inside the grid
    plt.legend(title="Statistical Parameters", loc='upper right', fontsize=14, framealpha=1, shadow=True, borderpad=1)
    
    plt.grid(True, which='both', linestyle=':', alpha=0.6)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_and_fit_peaks('Lk_new/allpeaks.csv')