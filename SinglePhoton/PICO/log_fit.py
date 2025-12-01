import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ----------------------------------------------------
# 1. CARICAMENTO DATI (Robusto con .iloc)
# ----------------------------------------------------
# Leggi dati dal CSV
df = pd.read_csv("dati_fit.csv")

# Usa gli indici per evitare KeyError
VDC = df.iloc[:, 0].values       # x
VFD = df.iloc[:, 1].values       # y
err_VFD = df.iloc[:, 2].values   # errori y

print(f"Dati caricati: {len(VDC)} punti.")

# ----------------------------------------------------
# 2. DEFINIZIONE DEL MODELLO A 3 PARAMETRI
# ----------------------------------------------------
def exp_model_3param(x, A, B, C):
    return A * np.exp(B * x) + C

# ----------------------------------------------------
# 3. ESECUZIONE DEL FIT
# ----------------------------------------------------

# GUESS INIZIALI (p0)
# È fondamentale darli per un fit a 3 parametri, altrimenti curve_fit potrebbe non convergere.
# Stime basate sui tuoi dati precedenti:
# C: Offset di base (sembra essere positivo per VDC bassi, es. ~40 mV)
# B: Pendenza esponenziale (era circa -0.06 nel fit precedente)
# A: Ampiezza (negativa molto piccola perché B è negativo e x è negativo grande)
p0_guess = [-1e-10, -0.06, 40] 

try:
    # Esegui il fit pesato (sigma=err_VFD)
    popt, pcov = curve_fit(exp_model_3param, VDC, VFD, sigma=err_VFD, absolute_sigma=True, p0=p0_guess, maxfev=20000)
    
    A, B, C = popt
    perr = np.sqrt(np.diag(pcov)) # Errori sui parametri

    print("-" * 40)
    print("RISULTATI FIT A 3 PARAMETRI: y = A * exp(Bx) + C")
    print("-" * 40)
    print(f"A = {A:.4e} ± {perr[0]:.4e}")
    print(f"B = {B:.6f} ± {perr[1]:.6f}")
    print(f"C = {C:.6f} ± {perr[2]:.6f}")
    print("-" * 40)

except RuntimeError as e:
    print("Errore: Il fit non è riuscito a convergere.")
    print("Prova a modificare i valori di p0_guess nello script.")
    print(e)
    exit()

# ----------------------------------------------------
# 4. PLOT DEI RISULTATI
# ----------------------------------------------------

# Genera dati per la curva fittata (ad alta risoluzione)
x_model = np.linspace(min(VDC), max(VDC), 1000)
y_model = exp_model_3param(x_model, A, B, C)

plt.figure(figsize=(10, 6))

# Plot dei dati originali
plt.errorbar(VDC, VFD, yerr=err_VFD, fmt='o', color='blue', ecolor='gray', 
             markersize=4, capsize=3, alpha=0.6, label='Dati Sperimentali')

# Plot del fit
plt.plot(x_model, y_model, 'r-', linewidth=2, label=f'Fit: $y = Ae^{{Bx}} + C$\n$C = {C:.2f}$')

plt.xlabel('VDC (mV)')
plt.ylabel('VFD (mV)')
plt.title('Fit Esponenziale a 3 Parametri')
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()

# Salva e mostra
plt.savefig('fit_esponenziale_3param.png')
plt.show()