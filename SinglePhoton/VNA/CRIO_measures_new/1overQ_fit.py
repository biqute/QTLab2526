import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import i0, k0

# --- COSTANTI FISICHE ---
k_B = 8.617333262145e-5  # Costante di Boltzmann (eV/K)
h = 4.135667696e-15      # Costante di Planck (eV s)

# --- CONFIGURAZIONE ---
file_path = "quality_factors.csv"         # Inserisci il nome del tuo file
colonna_da_fittare = "R1"      # Scegli quale colonna fittare (es. "R1", "R2")

# IMPORTANTE: Inserisci la frequenza di risonanza del tuo risonatore
# Qui ho impostato 4 GHz come esempio generico.
f0 = 7.492295e9  

# --- MODELLO MATEMATICO (Eq. 4.4, 2.28, 2.29) ---
def inverse_Qi_model(T_mK, inv_Qi_0, alpha, Delta_eV):
    """
    Modello per 1/Qi(T) basato sulla Teoria di Mattis-Bardeen.
    - inv_Qi_0: Dissipazione residua a T=0 (ovvero 1/Qi(0))
    - alpha: Frazione di induttanza cinetica
    - Delta_eV: Parametro di gap in eV
    """
    T = T_mK * 1e-3  # Converti la temperatura da mK a Kelvin
    
    # Parametro xi = hbar * omega / (2 * k_B * T) = h * f0 / (2 * k_B * T)
    xi = (h * f0) / (2 * k_B * T)
    
    # Calcolo del rapporto sigma1 / sigma2 dalle Eq. 2.28 e 2.29
    numeratore = np.exp(-Delta_eV / (k_B * T)) * np.sinh(xi) * k0(xi)
    denominatore = 1.0 - 2.0 * np.exp(-Delta_eV / (k_B * T)) * np.exp(-xi) * i0(xi)
    
    sigma_ratio = (4.0 / np.pi) * (numeratore / denominatore)
    
    # Eq. 4.4
    inv_Qi = inv_Qi_0 + (alpha / 2.0) * sigma_ratio
    
    return inv_Qi

# --- LETTURA DATI ---
df = pd.read_csv(file_path, sep=';', skipinitialspace=True)
df = df.dropna(axis=1, how='all')
df.columns = df.columns.str.strip()

# Rimuovi righe con valori mancanti per questa specifica colonna (es. i 200 mK in R5)
dati_validi = df[['T(mK)', colonna_da_fittare]].dropna()
T_data = dati_validi['T(mK)'].values
Qi_data = dati_validi[colonna_da_fittare].values

# Per il fit usiamo la dissipazione (1/Qi)
inv_Qi_data = 1.0 / Qi_data

# --- PREPARAZIONE DEL FIT ---
# Guess iniziali: [1/Qi(0), alpha, Delta_eV]
guess_iniziale = [1.0 / np.max(Qi_data), 0.5, 0.2e-3]

# Limiti (bounds) per forzare il fit ad avere senso fisico.
# Delta è limitato tra 0.05 meV e 1 meV, alpha tra 0 e 1.
limiti_inferiori = [0.0, 0.0, 0.05e-3]
limiti_superiori = [1e-3, 1.0, 1.0e-3]

print(f"Esecuzione del fit per la colonna {colonna_da_fittare}...")

try:
    popt, pcov = curve_fit(
        inverse_Qi_model, 
        T_data, 
        inv_Qi_data, 
        p0=guess_iniziale,
        bounds=(limiti_inferiori, limiti_superiori),
        maxfev=10000
    )
    perr = np.sqrt(np.diag(pcov))
    
    inv_Qi_0_fit, alpha_fit, Delta_fit = popt
    Qi_0_fit = 1.0 / inv_Qi_0_fit
    
    print("\n===== RISULTATI DEL FIT =====")
    print(f"Qi(0)          = {Qi_0_fit:.0f}")
    print(f"Alpha          = {alpha_fit:.4f} ± {perr[1]:.4f}")
    print(f"Delta (Gap)    = {Delta_fit*1e3:.4f} ± {perr[2]*1e3:.4f} meV")
    
    # --- PLOT DEI RISULTATI ---
    plt.figure(figsize=(9, 6))
    
    # Dati originali
    plt.plot(T_data, Qi_data, 'bo', label='Dati Sperimentali')
    
    # Curva fittata generata su una scala fitta per curvare in modo fluido
    T_fit_plot = np.logspace(np.log10(min(T_data)), np.log10(max(T_data)), 200)
    inv_Qi_fit_plot = inverse_Qi_model(T_fit_plot, *popt)
    Qi_fit_curve = 1.0 / inv_Qi_fit_plot
    
    plt.plot(T_fit_plot, Qi_fit_curve, 'r-', lw=2, label='Fit (Mattis-Bardeen)')
    
    # Formattazione Grafico
    plt.yscale('log')
    plt.xscale('log')
    plt.title(f'Andamento $Q_i(T)$ e Fit per {colonna_da_fittare}', fontsize=14)
    plt.xlabel('Temperatura T (mK)', fontsize=12)
    plt.ylabel('Fattore di Merito Interno $Q_i$', fontsize=12)
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(fontsize=12)
    
    plt.tight_layout()
    plt.show()

except RuntimeError:
    print("Errore: Il fit non è converguto. Potrebbe esserci troppa degenerazione tra alpha e Delta.")