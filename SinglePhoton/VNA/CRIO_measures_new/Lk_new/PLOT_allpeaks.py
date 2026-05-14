import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# 1. Target e Errore Frequenza
target_freqs = {'P1': 7.49, 'P3': 7.99, 'P4': 8.40, 'P5': 8.64}
f_err = 0.01  # Errore richiesto sulle frequenze [GHz]

def model(Lk, A, Lg):
    """f = A / sqrt(Lk + Lg)"""
    return A / np.sqrt(Lk + Lg)

def plot_and_fit_peaks(file_path):
    try:
        df = pd.read_csv(file_path, skipinitialspace=True)
    except FileNotFoundError:
        print(f"Errore: File '{file_path}' non trovato.")
        return

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.columns = df.columns.str.strip()
    peaks = ['P1', 'P3', 'P4', 'P5']
    df[peaks] = df[peaks].replace(0, np.nan)

    plt.figure(figsize=(15, 9))
    colors = plt.cm.tab10(np.linspace(0, 1, len(peaks)))
    lk_extrapolated_values = []

    for i, peak in enumerate(peaks):
        valid_data = df[['Lk', peak]].dropna()
        x_data, y_data = valid_data['Lk'].values, valid_data[peak].values
        
        if len(x_data) < 2: continue

        try:
            # Fit dei dati
            popt, pcov = curve_fit(model, x_data, y_data, p0=[30, 5])
            A_f, Lg_f = popt
            dA, dLg = np.sqrt(np.diag(pcov)) 

            # Estrapolazione Lk
            f_t = target_freqs[peak]
            lk_t = (A_f / f_t)**2 - Lg_f
            
            # Propagazione errore su Lk
            term_A = (2 * A_f / f_t**2) * dA
            term_f = (-2 * A_f**2 / f_t**3) * f_err
            term_Lg = dLg
            lk_err_prop = np.sqrt(term_A**2 + term_f**2 + term_Lg**2)
            
            lk_extrapolated_values.append(lk_t)

            # --- Plotting ---
            x_plot = np.linspace(0, max(x_data.max(), lk_t) * 1.1, 200)
            plt.plot(x_plot, model(x_plot, *popt), color=colors[i], linestyle='-', alpha=0.3)
            
            plt.errorbar(x_data, y_data, yerr=f_err, fmt='o', color=colors[i], 
                         markersize=4, capsize=3, alpha=0.3)

            # Proiezioni
            plt.plot([0, lk_t], [f_t, f_t], color=colors[i], linestyle='--', linewidth=0.8, alpha=0.5)
            plt.text(-0.2, f_t, f'{f_t}', color=colors[i], va='center', ha='right', fontsize=9)
            plt.plot([lk_t, lk_t], [0, f_t], color=colors[i], linestyle='--', linewidth=0.8, alpha=0.5)

            # Stella con errore
            plt.errorbar(lk_t, f_t, yerr=f_err, xerr=lk_err_prop, fmt='*', color='green', 
                         markersize=12, capsize=3, zorder=5)

        except Exception as e: print(f"Errore {peak}: {e}")

    # --- Calcolo Media, Dev Std e Regioni Colorate ---
    if lk_extrapolated_values:
        mean_lk = np.mean(lk_extrapolated_values)
        std_lk = np.std(lk_extrapolated_values)
        
        # Regione 2 sigma (lightblue) - tracciata per prima per rimanere sotto
        plt.axvspan(mean_lk - 2*std_lk, mean_lk + 2*std_lk, color='lightblue', alpha=0.3, 
                    label=r'Incertezza $2\sigma$ ($\pm$' + f'{2*std_lk:.2f})')
        
        # Regione 1 sigma (lightgreen) - tracciata sopra la 2 sigma
        plt.axvspan(mean_lk - std_lk, mean_lk + std_lk, color='lightgreen', alpha=0.4, 
                    label=r'Incertezza $1\sigma$ ($\pm$' + f'{std_lk:.2f})')
        
        # Linea verticale nera per la media
        plt.axvline(x=mean_lk, color='black', linestyle='--', linewidth=2, zorder=6,
                    label=f'$L_k$ = {mean_lk:.2f}')

        # Testo del valore Lk vicino alla linea tratteggiata
        y_lims = plt.gca().get_ylim()
        y_pos_text = y_lims[1] - (y_lims[1] - y_lims[0]) * 0.05 # Posizionato al 95% dell'altezza
        plt.text(mean_lk + 0.1, y_pos_text, f'$L_k$ = {mean_lk:.2f} $\pm$ {std_lk:.2f}',
                 color='black', fontweight='bold', fontsize=11, zorder=7,
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2))

    # Formattazione finale 
    plt.title(r'Estrapolazione $L_k$', fontsize=14)
    plt.xlabel(r'$L_k$', fontsize=12)
    plt.ylabel(r'$f_0$ (GHz)', fontsize=12)
    plt.xlim(left=-1.5)
    plt.ylim(bottom=min(target_freqs.values()) * 0.8)
    
    plt.legend(title="Legenda", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(True, which='both', linestyle=':', alpha=0.5)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_and_fit_peaks('Lk_new/allpeaks.csv')