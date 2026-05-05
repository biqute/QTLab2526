import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

# --- Modello Matematico ---
def LC_model(Lk, a, b, c):
    return a + b * 1/np.sqrt(Lk+c)

# Opzionale: impostazioni per il font
plt.rcParams.update({
    "text.usetex": False, # Metti True se hai LaTeX configurato
    "font.family": "Helvetica"
})

# Creazione cartella di output se non esiste (evita errori al salvataggio)
os.makedirs('sonnet_plots', exist_ok=True)

# --- Caricamento dati ---
data = np.loadtxt('sonnet_data/Resonance_vs_Lk.txt', skiprows=1)
Lk_values = data[:, 0]         # Lk in pH/sq
frequencies = data[:, 1]/1e9   # Frequenze in GHz

# --- Fit dei dati al modello LC ---
popt, pcov = curve_fit(LC_model, Lk_values, frequencies)
a_fit, b_fit, c_fit = popt

# =====================================================================
# --- ESTRAZIONE INDUTTANZA CINETICA (Target = 7.49 GHz) ---
# =====================================================================
f_target = 7.49

# Formula inversa: Lk = (b / (f_target - a))^2 - c
Lk_target = (b_fit / (f_target - a_fit))**2 - c_fit

print(f"\n--- RISULTATO ESTRAZIONE ---")
print(f"Frequenza Target: {f_target} GHz")
print(f"Induttanza Cinetica estratta (Lk): {Lk_target:.3f} pH/sq")
print(f"----------------------------\n")

# --- Dati per la linea continua del fit ---
Lk_fit = np.linspace(min(Lk_values)-0.5, max(Lk_values)+0.5, 200)
frequencies_fit = LC_model(Lk_fit, *popt)

# =====================================================================
# --- GRAFICO FREQUENZA VS Lk ---
# =====================================================================
fig, ax = plt.subplots(figsize=(8, 6))

# Plot dei dati simulati e della curva di fit
ax.plot(Lk_fit, frequencies_fit, '-', label='Fit', color='darkorange', alpha=0.9, lw=2.4)
ax.plot(Lk_values, frequencies, 'o', label='Simulated Data', color='navy', alpha=0.85, ms=5)

# Plot delle linee target (Croce di intersezione)
#ax.axhline(y=f_target, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
ax.axvline(x=Lk_target, color='red', linestyle='--', linewidth=2, alpha=0.8, 
           label=f'Target $L_k$ ({Lk_target:.2f} pH/sq)')

# Marcatore sul punto esatto di intersezione
ax.plot(Lk_target, f_target, '*', ms=14, zorder=5)

# Estetica del grafico (coerente con l'altro script)
ax.set_xlabel(r"Kinetic Inductance (pH/sq)", fontsize=12)
ax.set_ylabel(r"Resonance Frequency (GHz)", fontsize=12)
ax.grid(True, which='both', linestyle='--', alpha=0.6)
ax.legend(loc="best", fontsize=11)

fig.tight_layout()

# Salvataggio
fig.savefig('sonnet_plots/LC_fit.png', dpi=300, bbox_inches='tight')
fig.savefig('sonnet_plots/LC_fit.pdf', bbox_inches='tight')

plt.show()