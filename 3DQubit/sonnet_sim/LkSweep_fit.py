import sys
sys.path.append("../")
from circle_fit import CircleFitter
import numpy as np
from scipy import optimize
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from circle_fit import CircleFitter
import sys
import os

'''
Estrazione della frequenza di risonanza (e fattori di qualità) 
al variare dell'induttanza cinetica Lk da un file CSV esportato da Sonnet.
I fit individuali vengono salvati in file separati.
'''

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

#---Phase fit to get resonance f------
def theta_model(f, theta0, Qr, fr):
    return theta0 + 2*np.arctan( 2*Qr*(1.0 - f/fr) )

#---Complex model S21 notch----------
def S21_notch(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau):
    mod_QC = abs_Qc
    phi = phase_Qc
    return a * np.exp(1j*alpha)*np.exp(-1j* 2*np.pi*tau * f) * (1 - ((Ql/mod_QC) * np.exp(1j *phi))/(1 + 2j *Ql*(f/f0 -1)))

################ MAIN ########################

# Valori dell'induttanza cinetica da 0 a 15 con passo 1
Lk_values = np.arange(0, 16, 1)

fitter = CircleFitter()

# Array per conservare i risultati finali
Lk_val_num = []
fr_val = []
f_err_val = []

# --- Preparazione Grafico globale (Mag vs Freq per tutti gli Lk) ---
fig_all, ax_all = plt.subplots(figsize=(10, 6))
ax_all.set_xlabel(r"$f \ [GHz]$", fontsize=14)
ax_all.set_ylabel(r"$|S_{21}|$", fontsize=14)
ax_all.set_title("Resonances at different Kinetic Inductances ($L_k$)", fontsize=16)
ax_all.grid(True, alpha=0.3)

# Cartelle dove salvare i risultati (create se non esistono)
os.makedirs("Lk_results", exist_ok=True)
os.makedirs("Lk_results/individual_plots", exist_ok=True) 

# --- Caricamento e suddivisione dei dati dal CSV di Sonnet ---
print("Caricamento del file Lk_0.csv in corso...")
file_path = "sonnet_data/Lk_0.csv"
try:
    data_all = np.genfromtxt(file_path, delimiter=',', invalid_raise=False)
    data_all = data_all[~np.isnan(data_all[:, 0])] # Pulizia da NaN e righe di testo
except FileNotFoundError:
    print(f"ERRORE: File {file_path} non trovato. Interruzione.")
    sys.exit(1)

# Suddivisione in sweep individuali basata sui "salti" di frequenza
split_indices = np.where(np.diff(data_all[:, 0]) < 0)[0] + 1
data_sweeps = np.split(data_all, split_indices)

# Controllo sicurezza
if len(data_sweeps) != len(Lk_values):
    print(f"ATTENZIONE: Trovati {len(data_sweeps)} sweep nel CSV, ma ci si aspettava {len(Lk_values)} sweep (0-15).")
    # Limita l'iterazione al numero minimo per evitare crash
    max_iter = min(len(data_sweeps), len(Lk_values))
else:
    max_iter = len(Lk_values)

# ---------------- Ciclo su tutti gli Lk ----------------
for i in range(max_iter):
    Lk = Lk_values[i]
    data = data_sweeps[i]
    
    print(f"\n{'='*40}")
    print(f"--- Analyzing Lk: {Lk} pH/sq ---")
    print(f"{'='*40}")
    
    frequencies = data[:, 0]
    real_S21 = data[:, 5]     
    imag_S21 = data[:, 6]     

    signal = np.abs(real_S21 + 1j * imag_S21)
    phase = np.unwrap(np.angle(real_S21 + 1j * imag_S21))
    S21 = signal * np.exp(1j * phase)
    
    # Inizializziamo il plot globale per i dati RAW, così li vediamo sempre
    p = ax_all.plot(frequencies, abs(S21), 'o', ms=4, alpha=0.3, label=f"Lk = {Lk}")
    color = p[0].get_color()

    # --------- Analisi ed Estrazione dei Parametri ---------
    try:
        TAU = fitter._guess_delay(frequencies, S21)
        S21_calibrated = fitter._remove_cable_delay(frequencies, S21, TAU)
        tau_true = fitter._fit_delay(frequencies, S21_calibrated)
        S21_calibrated = fitter._remove_cable_delay(frequencies, S21_calibrated, tau_true)

        x_c, y_c, r_0 = fitter._fit_from_complex(S21_calibrated)
        S21_centered = fitter._center(S21_calibrated, x_c, y_c)
        phase_centered = np.unwrap(np.angle(S21_centered))

        # --- GESTIONE ERRORE MAXFEV SUL FIT LORENTZIANO ---
        try:
            f_r_guess, Q_r_guess = fitter._fit_lorentz(S21_calibrated, frequencies)
        except RuntimeError as e:
            print(f" -> ATTENZIONE: Fit Lorentz fallito ({e}).")
            print("    Uso stime geometriche di fallback.")
            # Se fallisce, usiamo il punto di minimo del segnale come frequenza
            f_r_guess = frequencies[np.argmin(np.abs(S21_calibrated))]
            Q_r_guess = 5000.0  # Valore di fallback generico

        # --- CORREZIONE DEI GUESS INIZIALI ---
        theta_0_guess_safe = np.angle(np.exp(1j * phase[np.argmin(signal)]))
        Q_r_guess_safe = max(1.0, min(Q_r_guess, 9.99e6))
        f_r_guess_safe = max(frequencies.min() + 1, min(f_r_guess, frequencies.max() - 1))

        # Fit della fase
        theta_0, Q_r, f_r = fitter._fit_phase(S21_centered, frequencies, theta_0_guess_safe, Q_r_guess_safe, f_r_guess_safe)
        beta = (theta_0 + np.pi) 
        P_off = x_c + r_0 * np.cos(beta)  + 1j*(y_c + r_0 * np.sin(beta))
        a_scaling = abs(P_off)  
        alpha = np.angle(P_off) 

        x_can, y_can, r_0_can = fitter._fit_from_complex(fitter._canonize(frequencies, S21, a_scaling, alpha, TAU + tau_true))

        Q_c_mag = Q_r * 2 * r_0_can
        phi_0 = -np.arcsin(y_can/r_0_can)
        Q_c = Q_r /(2 * r_0_can * np.exp( -1j * phi_0 ))
        Q_c_rev = 1/Q_c
        Q_i_rev = 1/Q_r - Q_c_rev.real
        Q_i = 1/Q_i_rev

        # --- Fit complesso S21 Notch ---
        S = signal * np.exp(1j * phase)
        
        try:
            params, pcov = fitter._fit_notch(S, frequencies, Q_r, Q_c, f_r, a_scaling, alpha, TAU + tau_true)
            Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit = params
            S_fit = S21_notch(frequencies, Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit)
            Q_c_fit = abs_Qc_fit * np.exp(1j * phase_Qc_fit)
            Q_c_rev = 1/Q_c_fit
            Q_i_rev = 1/Ql_fit - Q_c_rev.real
            f_r_err = np.sqrt(pcov[3, 3])
        except Exception as e:
            print(f" -> ATTENZIONE: Fit complesso fallito: {e}")
            f0_fit = f_r
            S_fit = S21_notch(frequencies, Q_r, abs(Q_c), np.angle(Q_c), f_r, a_scaling, alpha, TAU + tau_true)
            Q_c_fit = Q_c
            Q_i_rev = 1/Q_i
            
        print(f" -> Trovata f_r = {f0_fit:.6f} GHz")
        
        # --- Salvataggio dati SOLO se il fit è sopravvissuto ---
        Lk_val_num.append(Lk)
        fr_val.append(f0_fit)
        f_err_val.append(f_r_err)
        # Plot della curva fittata sul grafico globale
        ax_all.plot(frequencies, abs(S_fit), '-', lw=2.5, color=color)

        # =========================================================================
        # --- CREAZIONE E SALVATAGGIO DEL PLOT INDIVIDUALE ---
        # =========================================================================
        fig_indiv, (ax_mag, ax_phase) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
        
        ax_mag.plot(frequencies, abs(S), 'o', ms=4, alpha=0.5, color='blue', label='Data')
        ax_mag.plot(frequencies, abs(S_fit), '-', lw=2, color='red', label='Fit')
        ax_mag.set_ylabel(r"$|S_{21}|$", fontsize=14)
        ax_mag.set_title(f"Resonance Fit - Kinetic Inductance: {Lk} pH/sq", fontsize=15)
        ax_mag.grid(True, alpha=0.3)
        ax_mag.legend(loc='lower left')

        ax_phase.plot(frequencies, np.unwrap(np.angle(S)), 'o', ms=4, alpha=0.5, color='blue')
        ax_phase.plot(frequencies, np.unwrap(np.angle(S_fit)), '-', lw=2, color='red')
        ax_phase.set_ylabel(r"Phase [rad]", fontsize=14)
        ax_phase.set_xlabel(r"$f \ [GHz]$", fontsize=14)
        ax_phase.grid(True, alpha=0.3)

        fig_indiv.tight_layout()
        indiv_plot_name = f"Lk_results/individual_plots/Fit_Lk_{Lk}.pdf"
        fig_indiv.savefig(indiv_plot_name, bbox_inches="tight")
        plt.close(fig_indiv)

    except Exception as general_error:
        # Se anche il fallback fallisce o i dati non hanno senso (es. curva completamente piatta)
        # Salviamo la stampa a terminale e passiamo alla prossima curva
        print(f" -> CRITICO: Impossibile estrarre alcun parametro per Lk = {Lk}. Errore: {general_error}")
        print("    Salto questa curva e passo alla successiva.")
        continue

# --------- Salvataggio del grafico globale finale ---------
ax_all.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
fig_all.tight_layout()

plot_name = "Lk_results/All_Resonances_Fit.pdf"
fig_all.savefig(plot_name, bbox_inches="tight")
print(f"\nGrafico collettivo salvato in '{plot_name}'")

# --------- Salvataggio dei .txt ---------
# Lk vs Frequenza
txt_output_fr = "Lk_results/Resonance_vs_Lk.txt"
with open(txt_output_fr, "w") as file_txt:
    file_txt.write("Lk\tf_r_Hz\tf_r_err_GHz\n")
    for lk_n, fr_n, f_err_n in zip(Lk_val_num, fr_val, f_err_val):
        file_txt.write(f"{lk_n}\t{fr_n}\t{f_err_n}\n")
print(f"Frequenze di risonanza salvate in '{txt_output_fr}'")


plt.show()