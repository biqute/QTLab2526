import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv
import os 
#aa
# ==============================
# Funzione Lorentziana con offset
# ==============================
def lorentziana_offset(x, k, A, x0, gamma):
    """
    Lorentziana con offset:
    f(x) = k + A / (1 + ((x - x0)/gamma)^2)
    """
    return k + (A / (1 + ((x - x0) / gamma)**2))

# ==================================
# Funzione per leggere i dati dal CSV
# ==================================
def leggi_dati_csv(nome_file):
    frequenze = []
    ampiezze = []
    
    # Verifica se il file esiste
    if not os.path.isfile(nome_file):
        print(f"Errore: il file {nome_file} non esiste.")
        return None, None
    
    # Leggi il file CSV
    with open(nome_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Salta l'intestazione
        for row in reader:
            frequenze.append(float(row[0]))  # Colonna 1: frequenze
            ampiezze.append(float(row[3]))   # Colonna 4: ampiezza
    
    return np.array(frequenze), np.array(ampiezze)

# ==========================
# Richiesta del file CSV
# ==========================
nome_file = input("Inserisci il percorso del file CSV (ad esempio, 'data/dati_s11.csv'): ")

# Carica i dati
frequenze, ampiezze = leggi_dati_csv(nome_file)

if frequenze is None or ampiezze is None:
    print("File non trovato o errore nella lettura dei dati.")
else:
    # ==============================
    # Stima iniziale dei parametri
    # ==============================
    k_init = np.min(ampiezze)                           # Offset iniziale
    A_init = np.max(ampiezze) - np.min(ampiezze)        # Ampiezza iniziale
    x0_init = frequenze[np.argmax(ampiezze)]            # Centro del picco
    gamma_init = (np.max(frequenze) - np.min(frequenze)) / 10  # Larghezza stimata

    # ==============================
    # Fit Lorentziano
    # ==============================
    params, covariance = curve_fit(
        lorentziana_offset,
        frequenze,
        ampiezze,
        p0=[k_init, A_init, x0_init, gamma_init]
    )

    # Parametri ottimizzati
    k_opt, A_opt, x0_opt, gamma_opt = params

    # Errori sui parametri
    perr = np.sqrt(np.diag(covariance))
    k_err, A_err, x0_err, gamma_err = perr

    # ==============================
    # Calcolo chi-quadrato
    # ==============================
    ampiezza_fit = lorentziana_offset(frequenze, *params)
    chi_squared = np.sum(((ampiezze - ampiezza_fit) ** 2) / ampiezza_fit)
    N = len(frequenze)
    p = len(params)
    chi_squared_reduced = chi_squared / (N - p)

    # ==============================
    # Testo dei risultati
    # ==============================
    chi_text = f"$\\chi^2$ = {chi_squared:.5f}\n$\\chi^2_r$ = {chi_squared_reduced:.5f}"
    params_text = (f"$k$ = {k_opt:.6f} ± {k_err:.6f}\n"
                   f"$A$ = {A_opt:.6f} ± {A_err:.6f}\n"
                   f"$x_0$ = {x0_opt:.3f} ± {x0_err:.3f}\n"
                   f"$\\gamma$ = {gamma_opt:.3f} ± {gamma_err:.3f}")

    # ==============================
    # Grafico
    # ==============================
    plt.figure(figsize=(10, 6))
    plt.plot(frequenze, ampiezze, 'b.', label='Dati misurati')
    plt.plot(frequenze, ampiezza_fit, 'r-', label='Fit Lorentziano con offset')

    plt.text(0.95, 0.95, chi_text + "\n" + params_text,
             transform=plt.gca().transAxes, ha='right', va='top',
             fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

    plt.xlabel('Frequenza (Hz)')
    plt.ylabel('Ampiezza')
    plt.title('Fit Lorentziano con Offset dei Dati')
    plt.legend()
    plt.grid(True)
    plt.show()

