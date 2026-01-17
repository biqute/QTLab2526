import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# ==============================
# Funzione S21 (COMPLESSA)
# ==============================
def s21_notch_complex(f, a, alpha, tau, Ql, Qc, phi, fr): # <-- MODIFICA: Nome e logica
    """
    Calcola il valore COMPLESSO di S21.
    Parametri: (come prima)
    """
    numeratore = 1 - (Ql / Qc) * np.exp(1j * phi)
    denominatore = 1 + 2j * Ql * (f / fr - 1)
    S21 = a * np.exp(1j * alpha) * np.exp(-2j * np.pi * f * tau) * (numeratore / denominatore)
    return S21  # <-- MODIFICA: Restituisce il numero complesso

# ==============================
# Funzione "Wrapper" per il fit complesso
# ==============================
def s21_fit_wrapper(f_stacked, a, alpha, tau, Ql, Qc, phi, fr): # <-- MODIFICA: Nuova funzione
    """
    Wrapper per curve_fit per gestire dati complessi.
    Divide l'input f_stacked in frequenze, calcola S21 complesso,
    e restituisce un array 1D [reale1, reale2, ..., imm1, imm2, ...]
    """
    # Separa le frequenze (che sono duplicate)
    N = len(f_stacked) // 2
    f = f_stacked[:N]
    
    # Calcola il modello complesso
    s21_complex = s21_notch_complex(f, a, alpha, tau, Ql, Qc, phi, fr)
    
    # Restituisce le parti reali e immaginarie "impilate"
    return np.concatenate([s21_complex.real, s21_complex.imag])

# ==================================
# Funzione per leggere i dati (frequenza, reale, immaginaria)
# ==================================
def leggi_dati_complessi(nome_file): # <-- MODIFICA: Funzione riscritta
    """
    Legge un file di testo con colonne: frequenza, reale, immaginaria.
    Si assume che le colonne siano separate da spazi o tab.
    """
    if not os.path.isfile(nome_file):
        print(f"Errore: il file {nome_file} non esiste")
        return None, None, None
    
    try:
        # np.loadtxt è ideale per file di testo con colonne numeriche
        # unpack=True assegna ogni colonna a una variabile
        frequenze, parti_reali, parti_immaginarie = np.loadtxt(
            nome_file,
            unpack=True,
            comments='#' # Ignora righe che iniziano con #
        )
        return frequenze, parti_reali, parti_immaginarie
    except Exception as e:
        print(f"Errore durante la lettura del file {nome_file}: {e}")
        print("Assicurati che il file abbia 3 colonne numeriche (frequenza, reale, immaginaria).")
        return None, None, None

# ==========================
# Richiesta del file
# ==========================
# <-- MODIFICA: Cambiato il nome del file di esempio in .txt
#nome_file = input("Inserisci il percorso del file .txt (es. 'dati/miei_dati.txt'): ")
nome_file = "../data/misura_S21.txt"

frequenze, parti_reali, parti_immaginarie = leggi_dati_complessi(nome_file)

if frequenze is None:
    print("File non trovato o errore nella lettura dei dati.")
else:
    # Combina i dati in un array complesso per comodità
    dati_complessi = parti_reali + 1j * parti_immaginarie
    ampiezze_dati = np.abs(dati_complessi)

    # ==============================
    # Dati "impilati" per il fit
    # ==============================
    # curve_fit ha bisogno di array 1D reali.
    # Creiamo un array [reale1, ..., realeN, imm1, ..., immN]
    y_data_stacked = np.concatenate([parti_reali, parti_immaginarie])
    # Dobbiamo duplicare le frequenze per abbinare la lunghezza di y_data_stacked
    f_stacked = np.concatenate([frequenze, frequenze]) # <-- MODIFICA

    # ==============================
    # Stima iniziale dei parametri
    # ==============================
    # 'a' è l'ampiezza fuori risonanza
    a_init = np.median(ampiezze_dati) # <-- MODIFICA: 'median' è più robusto di 'max'
    alpha_init = 0.0
    tau_init = 0.0
    Ql_init = 1000.0
    Qc_init = 1000.0
    phi_init = 0.0
    # Per un NOTCH (minimo), usiamo argmin, non argmax
    fr_init = frequenze[np.argmin(ampiezze_dati)] # <-- MODIFICA: argmin

    p0 = [a_init, alpha_init, tau_init, Ql_init, Qc_init, phi_init, fr_init]

    # ==============================
    # Fit S21 notch
    # ==============================
    try:
        # Fittiamo usando la funzione wrapper e i dati impilati
        params, covariance = curve_fit(
            s21_fit_wrapper,  # <-- MODIFICA
            f_stacked,        # <-- MODIFICA
            y_data_stacked,   # <-- MODIFICA
            p0=p0,
            maxfev=20000 # Aumentato per fit complessi
        )
        a_opt, alpha_opt, tau_opt, Ql_opt, Qc_opt, phi_opt, fr_opt = params
        perr = np.sqrt(np.diag(covariance))

        # ==============================
        # Calcolo del fit (usando la funzione complessa originale)
        # ==============================
        s21_fit_complex = s21_notch_complex(frequenze, *params) # <-- MODIFICA
        ampiezza_fit = np.abs(s21_fit_complex)
        
        # ==============================
        # Calcolo chi-quadrato ridotto (basato su dati reali/immaginari)
        # ==============================
        # Calcoliamo i residui sui dati impilati
        residui_stacked = y_data_stacked - s21_fit_wrapper(f_stacked, *params) # <-- MODIFICA
        chi_squared = np.sum(residui_stacked**2) # Assumendo sigma=1
        
        N = len(y_data_stacked) # N ora è 2 * numero di punti
        p = len(params)
        chi_squared_reduced = chi_squared / (N - p)

        # ==============================
        # Testo dei risultati (invariato)
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
        # Grafico (Migliorato 2x2)
        # ==============================
        plt.figure(figsize=(12, 10)) # <-- MODIFICA: Figura più grande

        # --- Grafico 1: Ampiezza ---
        ax1 = plt.subplot(221)
        ax1.plot(frequenze, ampiezze_dati, 'b.', label='Dati (Ampiezza)', markersize=4)
        ax1.plot(frequenze, ampiezza_fit, 'r-', label='Fit (Ampiezza)')
        ax1.set_ylabel('Ampiezza')
        ax1.legend()
        ax1.grid(True)
        # Mostra i parametri nel primo grafico
        ax1.text(0.95, 0.95, chi_text + "\n\n" + params_text,
                 transform=ax1.transAxes, ha='right', va='top',
                 fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round,pad=0.5'))

        # --- Grafico 2: Fase ---
        ax2 = plt.subplot(222)
        # Usiamo unwrap per gestire i salti di fase di 2*pi
        ax2.plot(frequenze, np.unwrap(np.angle(dati_complessi)), 'b.', label='Dati (Fase)', markersize=4)
        ax2.plot(frequenze, np.unwrap(np.angle(s21_fit_complex)), 'r-', label='Fit (Fase)')
        ax2.set_ylabel('Fase (rad)')
        ax2.legend()
        ax2.grid(True)

        # --- Grafico 3: Parte Reale ---
        ax3 = plt.subplot(223)
        ax3.plot(frequenze, parti_reali, 'b.', label='Dati (Reale)', markersize=4)
        ax3.plot(frequenze, s21_fit_complex.real, 'r-', label='Fit (Reale)')
        ax3.set_xlabel('Frequenza (Hz)')
        ax3.set_ylabel('Parte Reale')
        ax3.legend()
        ax3.grid(True)
        
        # --- Grafico 4: Parte Immaginaria ---
        ax4 = plt.subplot(224)
        ax4.plot(frequenze, parti_immaginarie, 'b.', label='Dati (Immaginaria)', markersize=4)
        ax4.plot(frequenze, s21_fit_complex.imag, 'r-', label='Fit (Immaginaria)')
        ax4.set_xlabel('Frequenza (Hz)')
        ax4.set_ylabel('Parte Immaginaria')
        ax4.legend()
        ax4.grid(True)
        
        plt.suptitle('Fit S21 Notch (Complesso)', fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Aggiusta per il titolo
        plt.show()

    except RuntimeError as e:
        print(f"Errore: Fit non riuscito. Messaggio: {e}")
        print("Prova a migliorare le stime iniziali (p0) o ad aumentare 'maxfev'.")
    except Exception as e:
        print(f"Si è verificato un errore imprevisto: {e}")
