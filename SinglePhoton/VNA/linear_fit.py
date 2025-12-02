import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv
import os

# ==============================
# Funzione S21 con notch
# ============================== 
def retta(x, m, q):
    """
    Parametri:
    - m : coefficiente angolare
    - q : intercetta

    """
    
    retta = m*x + q
    return retta  # restituisce il modulo

# ==================================
# Funzione per leggere i dati dal CSV
# ==================================
def leggi_dati_csv(nome_file):
    frequenze = []
    fase = []
    
    
    if not os.path.isfile(nome_file):
        print(f"Errore: il file {nome_file} non esiste.")
        return None, None
    
    with open(nome_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Salta l'intestazione
        for row in reader:
            frequenze.append(float(row[0])) 
            fase.append(float(row[4]))  # Colonna 1: frequenze
              # Colonna 4: ampiezza (adatta se i tuoi dati sono in un'altra colonna)
    
    return np.array(frequenze), np.array(fase)

# ==========================
# Richiesta del file CSV
# ==========================
nome_file = input("Inserisci il percorso del file CSV (ad esempio, 'data/dati_s21.csv'): ")
frequenze, fase = leggi_dati_csv(nome_file)

if frequenze is None or fase is None:
    print("File non trovato o errore nella lettura dei dati.")
else:
    # ==============================
    # Selezione intervallo frequenze fino a 5.5 GHz
    # ==============================
    #
    # ==============================
    # Stima iniziale dei parametri
    # ==============================
    m = 0.0
    q = 0.0


    p0 = [m, q]

    # ==============================
    # Fit S21 notch
    # ==============================
    try:
        

        params, covariance = curve_fit(
        retta,
        frequenze,
        fase,
        p0=p0,
        maxfev=10000
)
        
        m_opt, q_opt = params
        perr = np.sqrt(np.diag(covariance))
        
        print(f"Risultati del fit lineare:")
        print(f"m = {m_opt:.6e} ± {perr[0]:.3e}")
        print(f"q = {q_opt:.3f} ± {perr[1]:.3f}")

        # Calcolo del fit
        fase_fit = retta(frequenze, *params)

        # ==============================
        # Calcolo chi-quadrato ridotto
        # ==============================
        chi_squared = np.sum(((fase - fase_fit) ** 2) )
        N = len(frequenze)
        p = len(params)
        chi_squared_reduced = chi_squared / (N - p)

        # ==============================
        # Testo dei risultati
        # ==============================
        chi_text = f"$\\chi^2$ = {chi_squared:.5f}\n$\\chi^2_r$ = {chi_squared_reduced:.5f}"
        params_text = (f"$m$ = {m_opt:.6e} ± {perr[0]:.3e}\n"
                       f"$q$ = {q_opt:.3f} ± {perr[1]:.3f}\n"
        )


        # ==============================
        # Grafico
        # ==============================
        plt.figure(figsize=(10, 6))
        plt.plot(frequenze, fase, 'b.', label='Dati misurati')
        plt.plot(frequenze, fase_fit, 'r-', label='Fit con una retta')

        plt.text(0.95, 0.95, chi_text + "\n" + params_text,
                 transform=plt.gca().transAxes, ha='right', va='top',
                 fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

        plt.xlabel('Frequenza (Hz)')
        plt.ylabel('fase')
        plt.title("Fit con una retta",
            fontsize=13
        )
        plt.legend()
        plt.grid(True)
        plt.show()

    except Exception as e:
        print(f"Errore durante il fit: {e}")
