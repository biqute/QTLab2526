import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# =========================================================
# 1. IMPOSTAZIONI DEL FILE E DELLE COLONNE
# =========================================================
file_excel = "fr_with_errors.xlsx" 

colonna_temperatura = "temp"      
colonna_frequenza = "fr_3"              
colonna_errore_frequenza = "sigma_fr_3" 

# =========================================================
# 2. DEFINIZIONE DELLA FUNZIONE DI FIT (Mattis-Bardeen)
# =========================================================
def f_vs_T(T_mK, f0, alpha, Delta_k):
    """
    T_mK    : Temperatura in milliKelvin
    f0      : Frequenza a T = 0 K
    alpha   : Frazione di induttanza cinetica
    Delta_k : Gap superconduttivo diviso per k_B (Delta / k_B) espresso in Kelvin
    """
    T_K = T_mK / 1000.0  # Convertiamo i mK in K
    
    # Preveniamo divisioni per zero se T scende a 0
    T_K = np.maximum(T_K, 1e-5) 
    
    # Termine di Mattis-Bardeen
    mb_term = (alpha / 2.0) * np.sqrt((np.pi * Delta_k) / (2.0 * T_K)) * np.exp(-Delta_k / T_K)
    
    # Assumiamo che la frequenza diminuisca con la temperatura
    return f0 * (1.0 - mb_term)

# Costante di Boltzmann in eV/K per convertire Delta alla fine
kB_eV = 8.617333262e-5

# =========================================================
# 3. LETTURA DATI E FIT
# =========================================================
try:
    print(f"Leggendo il file {file_excel}...")
    df = pd.read_excel(file_excel)
    df = df.dropna(subset=[colonna_temperatura, colonna_frequenza, colonna_errore_frequenza])
    df = df.sort_values(by=colonna_temperatura)

    # Estrazione array numpy
    temperature = df[colonna_temperatura].values
    frequenze = df[colonna_frequenza].values
    errori = df[colonna_errore_frequenza].values

    # Stime Iniziali (Guess) per aiutare il fit: [f0, alpha, Delta_k]
    # f0: la frequenza più alta registrata (a T più bassa)
    # alpha: tipicamente tra 0.01 e 0.1 per i MKID
    # Delta_k: ~2.0 K (tipico per l'alluminio)
    guess_iniziale = [np.max(frequenze), 0.05, 2.0]
    
    # Limiti per forzare i parametri ad avere un senso fisico
    # bounds=([f0_min, alpha_min, Delta_min], [f0_max, alpha_max, Delta_max])
    #limiti = ([np.min(frequenze), 1e-5, 0.1], [np.max(frequenze)*1.1, 1.0, 10.0])

    print("\nEsecuzione del Fit...")
    popt, pcov = curve_fit(
        f_vs_T, 
        temperature, 
        frequenze, 
        sigma=errori,          # Pesa il fit usando i tuoi errori sperimentali
        absolute_sigma=True,   # Indica che gli errori sono valori assoluti (non relativi)
        p0=guess_iniziale,
        #bounds=limiti,
        maxfev=10000
    )

    # Estrazione parametri ed errori
    f0_fit, alpha_fit, Delta_k_fit = popt
    f0_err, alpha_err, Delta_k_err = np.sqrt(np.diag(pcov))

    # Calcolo del Gap in micro-eV (µeV)
    Delta_ueV = Delta_k_fit * kB_eV * 1e6
    Delta_ueV_err = Delta_k_err * kB_eV * 1e6

    print("\n===== RISULTATI DEL FIT =====")
    print(f"f(0)   = {f0_fit:.6f} ± {f0_err:.6f} GHz")
    print(f"alpha  = {alpha_fit:.4e} ± {alpha_err:.4e}")
    print(f"Delta/kB = {Delta_k_fit:.4f} ± {Delta_k_err:.4f} K")
    print(f"--> Delta  = {Delta_ueV:.2f} ± {Delta_ueV_err:.2f} µeV")

    # =========================================================
    # 4. CREAZIONE DEL GRAFICO
    # =========================================================
    plt.figure(figsize=(9, 6))
    
    # Plot dei Dati Sperimentali
    plt.errorbar(temperature, frequenze, yerr=errori, 
                 fmt='o', markersize=6, color='black', 
                 ecolor='gray', elinewidth=1.5, capsize=4, label='Dati Sperimentali')
    
    # Generazione punti per tracciare la curva di Fit molto liscia
    T_smooth = np.linspace(min(temperature)*0.8, max(temperature)*1.05, 300)
    f_smooth = f_vs_T(T_smooth, *popt)
    
    # Plot della Curva di Fit
    plt.plot(T_smooth, f_smooth, '-', color='tab:red', linewidth=2.5, 
             label=f'Fit Mattis-Bardeen\n$\\alpha$ = {alpha_fit:.2e}\n$\\Delta$ = {Delta_ueV:.1f} $\\mu$eV')
    
    # Formattazione estetica
    plt.title("Fit Spostamento della Frequenza (Picco 2)", fontsize=14)
    plt.xlabel(colonna_temperatura, fontsize=12)
    plt.ylabel(colonna_frequenza, fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.show()

except FileNotFoundError:
    print(f"\nERRORE: Non riesco a trovare il file '{file_excel}'.")
except KeyError as e:
    print(f"\nERRORE: La colonna {e} non è presente nel file Excel.")
except RuntimeError:
    print("\nERRORE: L'algoritmo di Fit non è riuscito a convergere. Controlla che i dati siano puliti o prova a modificare il `guess_iniziale` nello script.")