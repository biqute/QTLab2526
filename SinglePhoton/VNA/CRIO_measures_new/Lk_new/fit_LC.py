import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# ==========================================
# 1. CARICAMENTO DATI DAL CSV ESISTENTE
# ==========================================
# Carica il file Frequenze_Minimi_3.csv (quello senza il punto 0.0)
df = pd.read_csv('Frequenze_Minimi.csv', sep=',')
df.columns = df.columns.str.strip()

# Estrazione degli array base
Lk_data = df['Lk'].values
f0_data = df['Frequenza_Minimo_GHz'].values

# ==========================================
# 2. INSERIMENTO MANUALE DEL PUNTO Lk=0.0
# ==========================================
# Aggiungiamo in cima agli array (posizione 0) i nuovi valori
Lk_data = np.insert(Lk_data, 0, 0.0)
f0_data = np.insert(f0_data, 0, 14.53)

print("Nuovo numero di punti dati:", len(Lk_data))

# Errore costante di 0.02 GHz su tutte le frequenze (incluso il nuovo punto)
sigma_f0 = np.full(len(f0_data), 0.02)

# ==========================================
# 3. DEFINIZIONE DEL MODELLO
# ==========================================
# Equazione di Thomson
def res_freq(Lk, Lgeo, C):
    return 1.0 / (2 * np.pi * np.sqrt((Lgeo + Lk) * C))

# ==========================================
# 4. FIT NON LINEARE
# ==========================================
popt, pcov = curve_fit(
    res_freq, 
    Lk_data, 
    f0_data, 
    p0=[5.0, 0.0001], 
    sigma=sigma_f0,
    absolute_sigma=True,
    bounds=([0, 0], [np.inf, np.inf])
)

Lgeo_opt = popt[0]
C_opt = popt[1]

# Incertezze 1-sigma
perr = np.sqrt(np.diag(pcov))
err_Lgeo = perr[0]
err_C = perr[1]

print("\n--- RISULTATI DEL FIT ---")
print(f"Lgeo = {Lgeo_opt:.4f} ± {err_Lgeo:.4f}")
print(f"C    = {C_opt:.7e} ± {err_C:.7e}")

# ==========================================
# 5. CALCOLO CHI-QUADRO
# ==========================================
f0_fit_points = res_freq(Lk_data, Lgeo_opt, C_opt)
residuals = f0_data - f0_fit_points
chi_squared = np.sum((residuals / sigma_f0)**2)
dof = len(f0_data) - len(popt)
reduced_chi_squared = chi_squared / dof

print("\n--- ANALISI STATISTICA ---")
print(f"Chi-quadro totale:  {chi_squared:.4f}")
print(f"Gradi di libertà:   {dof}")
print(f"Chi-quadro ridotto: {reduced_chi_squared:.4f}")

# ==========================================
# 6. ESTRAPOLAZIONE PUNTO TARGET
# ==========================================
f_target = 7.4922873822
Lk_estrapolato = (1.0 / ((2 * np.pi * f_target)**2 * C_opt)) - Lgeo_opt

print("\n--- ESTRAPOLAZIONE ---")
print(f"Frequenza Target:   {f_target} GHz")
print(f"Valore stimato Lk:  {Lk_estrapolato:.4f}")

# ==========================================
# 7. GRAFICO
# ==========================================
plt.figure(figsize=(10, 6))

# Dati sperimentali con barre di errore (includono automaticamente anche il punto a 0.0)
plt.errorbar(Lk_data, f0_data, yerr=sigma_f0, fmt='bo', capsize=3, 
             label='Dati (incluso $L_k=0.0$) ± 0.02 GHz')

# Curva di fit
Lk_fit = np.linspace(min(Lk_data), max(Lk_data), 100)
f0_fit = res_freq(Lk_fit, Lgeo_opt, C_opt)
label_fit = f'Fit:\n$L_{{geo}}={Lgeo_opt:.3f} \pm {err_Lgeo:.3f}$\n$\chi^2_{{rid}} = {reduced_chi_squared:.3f}$'
plt.plot(Lk_fit, f0_fit, 'r-', label=label_fit)

# Punto target estrapolato
plt.plot(Lk_estrapolato, f_target, 'g*', markersize=15, 
         label=f'Target $f={f_target:.2f} \Rightarrow L_k={Lk_estrapolato:.2f}$')

# Personalizzazione
plt.xlabel('$L_k$')
plt.ylabel('$f_0$ (GHz)')
plt.title('Fit Frequenza di Risonanza')
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.savefig('fit_LC_finale.png', dpi=300)
plt.show()