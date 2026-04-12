import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# =========================================================
# 1. DATI HARDCODED (Picco 1 rimosso, 300mK azzerati per 2, 4, 5)
# =========================================================
# Temperature in mK
T_all = np.array([11.95, 100.0, 200.0, 300.0])

# Dizionario con le frequenze (in GHz). 
# I valori 0.0 verranno ignorati dal fit.
frequenze_dict = {
    "Picco 2": np.array([7.812109, 7.812094, 7.812081, 0.0]),
    "Picco 3": np.array([7.992512, 7.992489, 7.992462, 7.992450]), # Mantiene i 300mK
    "Picco 4": np.array([8.397366, 8.397335, 8.397324, 0.0]),
    "Picco 5": np.array([8.637916, 8.637886, 8.637883, 0.0])
}

# Costante di Boltzmann in eV/K per convertire Delta
kB_eV = 8.617333262e-5

# =========================================================
# 2. DEFINIZIONE DELLA FUNZIONE DI FIT (Mattis-Bardeen)
# =========================================================
def f_vs_T(T_mK, f0, alpha, Delta_k):
    T_K = T_mK / 1000.0
    T_K = np.maximum(T_K, 1e-5) 
    mb_term = (alpha / 2.0) * np.sqrt((np.pi * Delta_k) / (2.0 * T_K)) * np.exp(-Delta_k / T_K)
    return f0 * (1.0 - mb_term)

# =========================================================
# 3. SETUP DELLA FIGURA MULTIPLA (2x2 Grid)
# =========================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 7))
axes = axes.flatten()

print(f"{'Risonanza':<10} | {'f(0) (GHz)':<12} | {'alpha':<12} | {'Delta (µeV)':<12}")
print("-" * 55)

# =========================================================
# 4. LOOP SUI 4 PICCHI RIMANENTI
# =========================================================
for i, (nome_picco, freq_array) in enumerate(frequenze_dict.items()):
    ax = axes[i]
    
    # Maschera per ignorare i valori 0.0 (dati mancanti o rimossi intenzionalmente)
    mask = freq_array > 0.0
    T_clean = T_all[mask]
    f_clean = freq_array[mask]
    
    # Creazione degli errori nominali (10 kHz) per i punti validi
    err_clean = np.full_like(f_clean, 0.000003)
    
    # Se non ci sono abbastanza punti, salta il fit
    if len(T_clean) < 2: # Abbassato a 2 per non far crashare se restano pochi punti
        ax.text(0.5, 0.5, 'Dati Insufficienti', ha='center', va='center')
        ax.set_title(f'{nome_picco} (Skipped)')
        continue

    # =========================================================
    # NUOVE STIME INIZIALI (Basate sul successo del Picco 3)
    # alpha = 3.0e-5, Delta = 20.2 µeV (che equivale a ~0.234 K)
    # =========================================================
    guess_iniziale = [np.max(f_clean), 3.0e-5, 0.234]
    
    # Limiti allargati verso il basso per alpha per evitare che si blocchi al limite
    limiti = ([np.min(f_clean), 1e-7, 0.01], [np.max(f_clean)*1.1, 1e-3, 10.0])

    try:
        # Esecuzione del Fit
        popt, pcov = curve_fit(
            f_vs_T, T_clean, f_clean, 
            sigma=err_clean, absolute_sigma=True, 
            p0=guess_iniziale, bounds=limiti, maxfev=10000
        )

        f0_fit, alpha_fit, Delta_k_fit = popt
        Delta_ueV = Delta_k_fit * kB_eV * 1e6
        
        # Stampa dei risultati in console
        print(f"{nome_picco:<10} | {f0_fit:.6f} | {alpha_fit:.2e} | {Delta_ueV:.2f}")

        # --- PREPARAZIONE DEL GRAFICO (IN kHz) ---
        f_ref = f_clean[0] # Riferimento a 11.95 mK
        
        delta_f_dati_kHz = (f_clean - f_ref) * 1e6
        err_kHz = err_clean * 1e6
        
        # Dati sperimentali
        ax.errorbar(T_clean, delta_f_dati_kHz, yerr=err_kHz, 
                    fmt='ko', markersize=6, ecolor='gray', elinewidth=1.5, 
                    capsize=4, label='Dati Sperimentali')
        
        # Curva di Fit (generata su tutto il range 10-310 mK per mostrare dove andrebbe la curva)
        T_smooth = np.linspace(10, 310, 300)
        f_smooth = f_vs_T(T_smooth, *popt)
        delta_f_fit_kHz = (f_smooth - f_ref) * 1e6
        
        ax.plot(T_smooth, delta_f_fit_kHz, '-', color='tab:red', linewidth=2.5, 
                label=f'MB Fit\n$\\alpha$ = {alpha_fit:.1e}\n$\\Delta$ = {Delta_ueV:.1f} $\\mu$eV')
        
        # Formattazione Subplot
        ax.set_title(f"Spostamento Frequenza ({nome_picco})", fontsize=12, fontweight='bold')
        ax.set_xlabel("Temperatura (mK)", fontsize=10)
        ax.set_ylabel("$\Delta f$ (kHz)", fontsize=10)
        ax.axhline(0, color='gray', linestyle=':', alpha=0.7)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(fontsize=9)

    except RuntimeError:
        ax.text(0.5, 0.5, f'Fit Fallito', ha='center', va='center')
        ax.set_title(f'{nome_picco} (Error)')
        print(f"{nome_picco:<10} | FIT FALLITO")

plt.savefig("MKID_Fits.png", dpi=300, bbox_inches='tight')
plt.tight_layout()
plt.show()