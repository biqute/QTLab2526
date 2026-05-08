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
Fits every data file in T_dep_data folder, extracts
resonance frequency and Q values, and plots them as
a function of temperature.
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

# Lista delle temperature
Temps = [
    "10mK",
    "200mK_b",
    "300mK_b",
    "400mK_b",  
    "500mK_b", "550mK_b", "600mK_b", "650mK_b", "675mK_b",
    "700mK", "725mK", "750mK", "775mK",
    "800mK", "825mK", "850mK", "875mK_b","900mK","925mK_b",
    "950mK", "975mK", "1000mK",
]

fitter = CircleFitter()

# Array per conservare i risultati finali e i relativi errori
revQ_val_num = []
err_revQ_val = []

Ql_val_num = []

Qc_val_num = []
err_abs_Qc_val = []
err_phase_Qc_val = []

T_val_num = []

fr_val = []
err_fr_val = []

# --- Preparazione Grafico globale (Mag vs Freq per tutte le T) ---
fig_all, ax_all = plt.subplots(figsize=(10, 6))
ax_all.set_xlabel(r"$f \ [GHz]$", fontsize=14)
ax_all.set_ylabel(r"$|S_{21}|$", fontsize=14)
ax_all.set_title("Resonances at different Temperatures", fontsize=16)
ax_all.grid(True, alpha=0.3)

# Cartelle dove salvare i risultati (create se non esistono)
os.makedirs("T_dep_results", exist_ok=True)
os.makedirs("T_dep_results/individual_plots", exist_ok=True)

# ---------------- Ciclo su tutte le Temperature ----------------
for t in Temps:
    print(f"\n{'='*40}")
    print(f"--- Analyzing Temperature: {t} ---")
    print(f"{'='*40}")
    
    # Rimuovi "mK" dalla stringa per salvare il numero nel file di output
    new_t = t.replace("_b", "")
    T_num = float(new_t.replace("mK", ""))
    
    # Caricamento del dataset
    file_path = f"T_dep_data/2_MKID_resonance_{t}.txt"
    try:
        data = np.loadtxt(file_path, delimiter="\t")
    except FileNotFoundError:
        print(f"ATTENZIONE: File {file_path} non trovato. Salto questa temperatura...")
        continue

    frequencies = data[:, 0]/1e9  # Frequenze in GHz
    real_S21 = data[:, 1]     # Parte reale di S21
    imag_S21 = data[:, 2]     # Parte immaginaria di S21

    signal = np.abs(real_S21 + 1j * imag_S21)
    phase = np.unwrap(np.angle(real_S21 + 1j * imag_S21))

    S21 = signal * np.exp(1j * phase)

    # --------- Analisi ed Estrazione dei Parametri ---------
    TAU = fitter._guess_delay(frequencies, S21)
    S21_calibrated = fitter._remove_cable_delay(frequencies, S21, TAU)
    tau_true = fitter._fit_delay(frequencies, S21_calibrated)
    S21_calibrated = fitter._remove_cable_delay(frequencies, S21_calibrated, tau_true)

    x_c, y_c, r_0 = fitter._fit_from_complex(S21_calibrated)
    S21_centered = fitter._center(S21_calibrated, x_c, y_c)
    phase_centered = np.unwrap(np.angle(S21_centered))

    f_r_guess, Q_r_guess = fitter._fit_lorentz(S21_calibrated, frequencies)

    # --- CORREZIONE DEI GUESS INIZIALI ---
    # 1. Riavvolge la fase strettamente tra -pi e pi per evitare sforamenti
    theta_0_guess_safe = np.angle(np.exp(1j * phase[np.argmin(signal)]))

    # 2. Clampa la stima di Q_r affinché stia strettamente tra 1 e 9.99 milioni
    Q_r_guess_safe = max(1.0, min(Q_r_guess, 9.99e6))

    # 3. Assicura che la stima della frequenza sia strettamente dentro i margini misurati
    f_r_guess_safe = max(frequencies.min() + 1e-6, min(f_r_guess, frequencies.max() - 1e-6))

    # Fit della fase in totale sicurezza:
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

    # --- Fit complesso ---
    S = signal * np.exp(1j * phase)
    
    # Blocco try-except inserito per T molto alte
    try:
        params, pcov = fitter._fit_notch(S, frequencies, Q_r, Q_c, f_r, a_scaling, alpha, TAU + tau_true)
        Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit = params
        S_fit = S21_notch(frequencies, Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit)
        
        # --- ESTRAZIONE ERRORI DALLA COVARIANZA ---
        perr = np.sqrt(np.diag(pcov))
        err_Ql = perr[0]
        err_abs_Qc = perr[1]
        err_phase_Qc = perr[2]
        err_f0 = perr[3]
        
        # Propagazione errore per 1/Qi = 1/Ql - cos(phase_Qc)/abs_Qc
        J_revQi = np.array([
            -1.0 / Ql_fit**2,
            np.cos(phase_Qc_fit) / abs_Qc_fit**2,
            np.sin(phase_Qc_fit) / abs_Qc_fit
        ])
        sub_pcov = pcov[0:3, 0:3]
        err_revQi = np.sqrt(np.abs(np.dot(J_revQi, np.dot(sub_pcov, J_revQi))))

    except Exception as e:
        print(f"Fit complesso fallito per {t}: {e}\nUso f_r dallo step di fit in fase.")
        f0_fit = f_r
        S_fit = S21_notch(frequencies, Q_r, abs(Q_c), np.angle(Q_c), f_r, a_scaling, alpha, TAU + tau_true)
        
        # Gestione fallback per gli errori
        err_f0 = 0.0
        err_revQi = 0.0
        err_abs_Qc = 0.0
        err_phase_Qc = 0.0

    print(f" -> Trovata f_r = {f0_fit:.6f} GHz ± {err_f0:.2e}")
    
    # --- Calcolo del Q valore
    Q_c_fit = abs_Qc_fit * np.exp(1j * phase_Qc_fit)
    Q_c_rev = 1/Q_c_fit
    Q_i_rev = 1/Ql_fit - Q_c_rev.real
    
    # --- Salvataggio dati e propagazione errori finali ---
    T_val_num.append(T_num)
    
    fr_val.append(f0_fit)
    err_fr_val.append(err_f0)
    
    revQ_val_num.append(Q_i_rev)
    err_revQ_val.append(err_revQi)
    
    Qc_val_num.append(Q_c_fit)
    err_abs_Qc_val.append(err_abs_Qc)
    err_phase_Qc_val.append(err_phase_Qc)
    
    # --- Popoliamo il plot GLOBALE ---
    p = ax_all.plot(frequencies, abs(S), 'o', ms=4, alpha=0.3, label=f"Data {t}")
    color = p[0].get_color()
    ax_all.plot(frequencies, abs(S_fit), '-', lw=2.5, color=color)

    # =========================================================================
    # --- PLOT INDIVIDUALE PER QUESTA T ---
    # =========================================================================
    fig_indiv, (ax_mag, ax_phase) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    
    # Modulo
    ax_mag.plot(frequencies, abs(S), 'o', ms=4, alpha=0.5, color='blue', label='Data')
    ax_mag.plot(frequencies, abs(S_fit), '-', lw=2, color='red', label='Fit')
    ax_mag.set_ylabel(r"$|S_{21}|$", fontsize=14)
    ax_mag.set_title(f"Resonance Fit - Temperature: {t}", fontsize=15)
    ax_mag.grid(True, alpha=0.3)
    ax_mag.legend(loc='lower left')

    # Fase
    ax_phase.plot(frequencies, np.unwrap(np.angle(S)), 'o', ms=4, alpha=0.5, color='blue')
    ax_phase.plot(frequencies, np.unwrap(np.angle(S_fit)), '-', lw=2, color='red')
    ax_phase.set_ylabel(r"Phase [rad]", fontsize=14)
    ax_phase.set_xlabel(r"$f \ [GHz]$", fontsize=14)
    ax_phase.grid(True, alpha=0.3)

    fig_indiv.tight_layout()
    
    # Salviamo il file PDF nella nuova cartella
    indiv_plot_name = f"T_dep_results/individual_plots/Fit_{t}.pdf"
    fig_indiv.savefig(indiv_plot_name, bbox_inches="tight")
    
    # CHIUDIAMO LA FIGURA
    plt.close(fig_indiv)
    # =========================================================================

# --------- Salvataggio del grafico globale finale ---------
ax_all.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
fig_all.tight_layout()

plot_name = "T_dep_results/All_Resonances_Fit.pdf"
fig_all.savefig(plot_name, bbox_inches="tight")
print(f"\nGrafico collettivo salvato in '{plot_name}'")

# --------- Salvataggio del .txt (Temperatura vs Frequenza con Errori) ---------
txt_output = "T_dep_results/Resonance_vs_Temperature.txt"
with open(txt_output, "w") as file_txt:
    file_txt.write("T_mK\tf_r_GHz\terr_f_r\n")
    for t_n, fr_n, err_fr_n in zip(T_val_num, fr_val, err_fr_val):
        file_txt.write(f"{t_n}\t{fr_n}\t{err_fr_n}\n")

print(f"Risultati tabellati salvati in '{txt_output}'\n")

# --------- Salvataggio del .txt (1/Q vs Temperature con Errori) ---------
txt_output = "T_dep_results/revQ_vs_Temperature.txt"
with open(txt_output, "w") as file_txt:
    file_txt.write("T_mK\trevQ_i\terr_revQ_i\n")
    for t_n, revQ_n, err_revQ_n in zip(T_val_num, revQ_val_num, err_revQ_val):
        file_txt.write(f"{t_n}\t{revQ_n}\t{err_revQ_n}\n")

# --------- Salvataggio del .txt (Qc vs Temperature con Errori Modulo/Fase) ---------
txt_output = "T_dep_results/Qc_vs_Temperature.txt"
with open(txt_output, "w") as file_txt:
    file_txt.write("T_mK\tQ_c_complex\t|Q_c|\terr_|Q_c|\tPhase_Q_c\terr_Phase\n")
    for t_n, Qc_n, err_abs, err_ph in zip(T_val_num, Qc_val_num, err_abs_Qc_val, err_phase_Qc_val):
        file_txt.write(f"{t_n}\t{Qc_n}\t{np.abs(Qc_n)}\t{err_abs}\t{np.angle(Qc_n)}\t{err_ph}\n")

print(f"Risultati tabellati salvati in '{txt_output}'\n")

# Mostra il grafico globale finale a schermo
plt.show()