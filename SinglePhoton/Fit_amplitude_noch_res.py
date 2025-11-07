import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv
import os

# ==============================
# Funzione S21 con notch
# ==============================
def s21_notch(f, a, alpha, tau, Ql, Qc, phi, fr):
    """
    Parametri:
    - f : array delle frequenze [Hz]
    - a : ampiezza globale
    - alpha : fase globale [rad]
    - tau : ritardo [s]
    - Ql : qualità totale
    - Qc : qualità di accoppiamento (modulo)
    - phi : fase di accoppiamento [rad]
    - fr : frequenza di risonanza [Hz]
    """
    numeratore = 1 - (Ql / Qc) * np.exp(1j * phi)
    denominatore = 1 + 2j * Ql * (f / fr - 1)
    S21 = a * np.exp(1j * alpha) * np.exp(-2j * np.pi * f * tau) * (numeratore / denominatore)
    return np.abs(S21)  # restituisce il modulo

# ==================================
# Funzione per leggere i dati dal CSV
# ==================================
def leggi_dati_csv(nome_file):
    frequenze = []
    ampiezze = []
    
    if not os.path.isfile(nome_file):
        print(f"Errore: il file {nome_file} non esiste.")
        return None, None
    
    with open(nome_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Salta l'intestazione
        for row in reader:
            frequenze.append(float(row[0]))  # Colonna 1: frequenze
            ampiezze.append(float(row[3]))   # Colonna 4: ampiezza (adatta se i tuoi dati sono in un'altra colonna)
    
    return np.array(frequenze), np.array(ampiezze)

# ==========================
# Richiesta del file CSV
# ==========================
nome_file = input("Inserisci il percorso del file CSV (ad esempio, 'data/dati_s21.csv'): ")
frequenze, ampiezze = leggi_dati_csv(nome_file)

if frequenze is None or ampiezze is None:
    print("File non trovato o errore nella lettura dei dati.")
else:
    # ==============================
    # Stima iniziale dei parametri
    # ==============================
    a_init = np.max(ampiezze)
    alpha_init = 0.0
    tau_init = 0.0
    Ql_init = 1000.0
    Qc_init = 1000.0
    phi_init = 0.0
    fr_init = frequenze[np.argmax(ampiezze)]

    p0 = [a_init, alpha_init, tau_init, Ql_init, Qc_init, phi_init, fr_init]

    # ==============================
    # Fit S21 notch
    # ==============================
    try:
        params, covariance = curve_fit(s21_notch, frequenze, ampiezze, p0=p0, maxfev=10000)
        a_opt, alpha_opt, tau_opt, Ql_opt, Qc_opt, phi_opt, fr_opt = params
        perr = np.sqrt(np.diag(covariance))

        # Calcolo del fit
        ampiezza_fit = s21_notch(frequenze, *params)

        # ==============================
        # Calcolo chi-quadrato ridotto
        # ==============================
        chi_squared = np.sum(((ampiezze - ampiezza_fit) ** 2) / ampiezza_fit)
        N = len(frequenze)
        p = len(params)
        chi_squared_reduced = chi_squared / (N - p)

        # ==============================
        # Testo dei risultati
        # ==============================
        chi_text = f"$\\chi^2$ = {chi_squared:.5f}\n$\\chi^2_r$ = {chi_squared_reduced:.5f}"
        params_text = (f"$a$ = {a_opt:.6f} ± {perr[0]:.6f}\n"
                       f"$\\alpha$ = {alpha_opt:.6f} ± {perr[1]:.6f}\n"
                       f"$\\tau$ = {tau_opt:.6e} ± {perr[2]:.6e}\n"
                       f"$Q_l$ = {Ql_opt:.3f} ± {perr[3]:.3f}\n"
                       f"$Q_c$ = {Qc_opt:.3f} ± {perr[4]:.3f}\n"
                       f"$\\phi$ = {phi_opt:.3f} ± {perr[5]:.3f}\n"
                       f"$f_r$ = {fr_opt:.3f} ± {perr[6]:.3f}")

        # ==============================
        # Grafico
        # ==============================
        plt.figure(figsize=(10, 6))
        plt.plot(frequenze, ampiezze, 'b.', label='Dati misurati')
        plt.plot(frequenze, ampiezza_fit, 'r-', label='Fit S21 notch')

        plt.text(0.95, 0.95, chi_text + "\n" + params_text,
                 transform=plt.gca().transAxes, ha='right', va='top',
                 fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

        plt.xlabel('Frequenza (Hz)')
        plt.ylabel('Ampiezza')
        plt.title('Fit S21 Notch dei Dati')
        plt.legend()
        plt.grid(True)
        plt.show()

    except Exception as e:
        print(f"Errore durante il fit: {e}")
