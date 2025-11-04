import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv
import os

# Funzione gaussiana con offset (parametro k)
def gaussiana_offset(x, k, A, mu, sigma):
    return k + A * np.exp(- (x - mu)**2 / (2 * sigma**2))

# Funzione per leggere i dati dal file CSV
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
            ampiezze.append(float(row[3]))  # Colonna 4: ampiezza
    
    return np.array(frequenze), np.array(ampiezze)

# Chiedi il percorso del file CSV all'utente
nome_file = input("Inserisci il percorso del file CSV (ad esempio, 'data/dati_s11.csv'): ")

# Carica i dati dal CSV
frequenze, ampiezze = leggi_dati_csv(nome_file)

if frequenze is None or ampiezze is None:
    print("File non trovato o errore nella lettura dei dati.")
else:
    # Stima iniziale per A, mu, sigma, e k
    A_init = np.max(ampiezze)  # Ampiezza iniziale (picco)
    mu_init = frequenze[np.argmax(ampiezze)]  # Posizione del picco
    sigma_init = np.std(frequenze)  # Deviazione standard iniziale (larghezza del picco)
    k_init = np.min(ampiezze)  # Offset iniziale (valore minimo delle ampiezze)

    # Adatta la curva gaussiana ai dati
    params, covariance = curve_fit(gaussiana_offset, frequenze, ampiezze, p0=[k_init, A_init, mu_init, sigma_init])

    # Parametri ottimizzati
    k_opt, A_opt, mu_opt, sigma_opt = params

    # Calcola gli errori sui parametri (dalla diagonale della matrice di covarianza)
    perr = np.sqrt(np.diag(covariance))
    k_err, A_err, mu_err, sigma_err = perr

    # Calcola il chi-quadrato (χ²)
    ampiezza_fit = gaussiana_offset(frequenze, *params)
    chi_squared = np.sum(((ampiezze - ampiezza_fit) ** 2) / ampiezza_fit)  # Somma dei quadrati normalizzati

    # Calcola il chi-quadrato ridotto (χ²_r)
    N = len(frequenze)  # Numero di dati
    p = len(params)  # Numero di parametri (4 per la gaussiana con offset)
    chi_squared_reduced = chi_squared / (N - p)  # Chi-quadrato ridotto

    # Parametri per il testo da visualizzare nel box
    chi_text = f"$\\chi^2$ = {chi_squared:.5f}\n$\\chi^2_r$ = {chi_squared_reduced:.5f}"
    params_text = (f"$k$ = {k_opt:.6f} ± {k_err:.6f}\n"
                   f"$A$ = {A_opt:.6f} ± {A_err:.6f}\n"
                   f"$\\mu$ = {mu_opt:.3f} ± {mu_err:.3f}\n"
                   f"$\\sigma$ = {sigma_opt:.3f} ± {sigma_err:.3f}")

    # Plot dei dati originali e della curva gaussiana adattata
    plt.figure(figsize=(10, 6))
    plt.plot(frequenze, ampiezze, 'b.', label='Dati misurati')
    plt.plot(frequenze, ampiezza_fit, 'r-', label='Fit Gaussiano con offset')

    # Aggiungi il box con il chi-quadrato e i parametri
    plt.text(0.95, 0.95, chi_text + "\n" + params_text,
             transform=plt.gca().transAxes, ha='right', va='top',
             fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

    # Etichette e titoli
    plt.xlabel('Frequenza (Hz)')
    plt.ylabel('Ampiezza')
    plt.title('Fit Gaussiano con Offset dei Dati')
    plt.legend()
    plt.grid(True)
    plt.show()
