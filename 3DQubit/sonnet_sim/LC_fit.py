import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

# --- Modello Matematico ---
def LC_model(Lk, a, b, c):
    return a + b * 1/np.sqrt(Lk+c)

########## IMPOSTAZIONI GRAFICHE (Aesthetic Improvements) #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica",
    "axes.labelsize": 16,        # Dimensione label assi x e y
    "axes.titlesize": 18,        # Dimensione titolo
    "xtick.labelsize": 12,       # Dimensione tick x
    "ytick.labelsize": 12,       # Dimensione tick y
    "legend.fontsize": 14,       # Dimensione legenda
    "lines.linewidth": 2         # Spessore delle linee di default
})

# Creazione cartella di output se non esiste (evita errori al salvataggio)
os.makedirs('sonnet_plots', exist_ok=True)

# --- Caricamento dati ---
data = np.loadtxt('Lk_results/Resonance_vs_Lk.txt', skiprows=1)
Lk_values = data[:, 0]         # Lk in pH/sq
frequencies = data[:, 1]
freq_err = data[:, 2]          # Errori sulle frequenze in GHz

# --- Fit dei dati al modello LC ---
from iminuit import Minuit
from iminuit.cost import LeastSquares

# Assicurati che model sia definita come: model(x, inv_Qi_0, Delta)
# 1. Definiamo la funzione di costo corretta
# Usiamo 'y_errors' al posto di 'yerr'
cost_func = LeastSquares(Lk_values, frequencies, freq_err, LC_model)
p0 = [0.03, 32.6, 5.02]  # Stima iniziale per [a, b, c]
# 2. Inizializziamo Minuit
# esattamente con quelli usati nella definizione di 'model'
m = Minuit(cost_func, a=p0[0], b=p0[1], c=p0[2])

# 3. Impostiamo i limiti


# 4. Fit
m.migrad()  # Trova il minimo
m.hesse()   # Calcola gli errori parabolici

# 5. Estrazione risultati
a_fit = m.values["a"]
b_fit = m.values["b"]
c_fit = m.values["c"]
a_err = m.errors["a"]
b_err = m.errors["b"]
c_err = m.errors["c"]

print(m)

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
frequencies_fit = LC_model(Lk_fit, a_fit, b_fit, c_fit)

# =====================================================================
# --- GRAFICO FREQUENZA VS Lk ---
# =====================================================================
fig, ax = plt.subplots(figsize=(8, 6))

# Plot dei dati simulati e della curva di fit
ax.plot(Lk_fit, frequencies_fit, '-', label='Fit', color='darkorange', alpha=0.9, lw=2.4)
ax.errorbar(Lk_values, frequencies, yerr = freq_err*10, fmt='o', label='Simulated Data', color='navy', alpha=0.85, ms=5)

# Plot delle linee target (Croce di intersezione)
#ax.axhline(y=f_target, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
ax.axvline(x=Lk_target, color='red', linestyle='--', linewidth=2, alpha=0.8, 
           label=f'Target $L_k$ ({Lk_target:.2f} pH/sq)')

# Marcatore sul punto esatto di intersezione
ax.plot(Lk_target, f_target, '*', ms=14, zorder=5)

# Estetica del grafico (coerente con l'altro script)
ax.set_xlabel(r"Kinetic Inductance (pH/sq)")
ax.set_ylabel(r"Resonance Frequency (GHz)",)
ax.grid(True, which='both', linestyle='--', alpha=0.6)
ax.legend(loc="best", fontsize=14)

fig.tight_layout()

# Salvataggio
fig.savefig('sonnet_plots/LC_fit.png', dpi=300, bbox_inches='tight')
fig.savefig('sonnet_plots/LC_fit.pdf', bbox_inches='tight')

plt.show()