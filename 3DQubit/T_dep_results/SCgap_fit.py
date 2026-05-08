import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import i0, k0
from iminuit import Minuit
from iminuit.cost import LeastSquares
from iminuit.util import describe

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

#def model(T, a, b, Delta):
#    # Boltzmann constant in eV/mK: (J/K) * (1/ (J/eV)) * (1 K / 1000 mK)
#    k_B = 8.617333e-5 / 1000  
#    return a + b * np.exp(-Delta / (k_B * T))

# --- COSTANTI FISICHE ---
k_B = 8.617333262145e-5  # Costante di Boltzmann (eV/K)
h = 4.135667696e-15      # Costante di Planck (eV s)
alpha = 0.7354
f_0 = 7.49e9

def model(T_mK, inv_Qi_0, Delta_eV):
    """
    Modello per 1/Qi(T) basato sulla Teoria di Mattis-Bardeen.
    - inv_Qi_0: Dissipazione residua a T=0 (ovvero 1/Qi(0))
    - alpha: Frazione di induttanza cinetica
    - Delta_eV: Parametro di gap in eV
    """
    T = T_mK * 1e-3  # Converti la temperatura da mK a Kelvin
    
    # Parametro xi = hbar * omega / (2 * k_B * T) = h * f0 / (2 * k_B * T)
    xi = (h * f_0) / (2 * k_B * T)
    
    # Calcolo del rapporto sigma1 / sigma2 dalle Eq. 2.28 e 2.29
    numeratore = np.exp(-Delta_eV / (k_B * T)) * np.sinh(xi) * k0(xi)
    denominatore = 1.0 - 2.0 * np.exp(-Delta_eV / (k_B * T)) * np.exp(-xi) * i0(xi)
    
    sigma_ratio = (4.0 / np.pi) * (numeratore / denominatore)
    
    # Eq. 4.4
    inv_Qi = inv_Qi_0 + (alpha / 2.0) * sigma_ratio
    
    return inv_Qi

# Caricamento dati
data = np.loadtxt("revQ_vs_Temperature.txt", skiprows=1)
temp = data[:,0]
revQ = data[:,1]
revQ_err = data[:,2]

p0 = [revQ[0], 0.002]  # Stima iniziale per [inv_Qi_0, Delta_eV]
lower = [0, 0]     # Limiti inferiori per i parametri
upper = [1e-3, 1]  # Limiti superiori per i parametri
from iminuit import Minuit
from iminuit.cost import LeastSquares

# Assicurati che model sia definita come: model(x, inv_Qi_0, Delta)
# 1. Definiamo la funzione di costo corretta
# Usiamo 'y_errors' al posto di 'yerr'
cost_func = LeastSquares(temp, revQ, revQ_err, model)

# 2. Inizializziamo Minuit
# Nota: i nomi dei parametri (inv_Qi_0, Delta) devono coincidere 
# esattamente con quelli usati nella definizione di 'model'
m = Minuit(cost_func, inv_Qi_0=p0[0], Delta_eV=p0[1])

# 3. Impostiamo i limiti
m.limits["inv_Qi_0"] = (lower[0], upper[0])
m.limits["Delta_eV"] = (lower[1], upper[1])

# 4. Fit
m.migrad()  # Trova il minimo
m.hesse()   # Calcola gli errori parabolici

# 5. Estrazione risultati
inv_Q0_fit = m.values["inv_Qi_0"]
Delta_fit = m.values["Delta_eV"]
Delta_err = m.errors["Delta_eV"]

print(m)

T_c = Delta_fit/(1.764 * k_B)

print(f"Critical temperature T_c = {T_c:.4f} K")
print(f"Superconducting Gap = {Delta_fit*1e3:.4f} pm  meV")

# Prepara i dati per il plot del fit
x_fit = np.linspace(np.min(temp), np.max(temp), 100)
f_fit = model(x_fit,inv_Q0_fit, Delta_fit)

lw_style = 2     # Spessore standard
alpha_style = 0.7   # Leggera trasparenza per chiarezza visiva
zorder_style = 1

plt.figure(figsize=(8, 6))
plt.errorbar(temp, revQ, yerr=revQ_err*20, fmt='o', label="Data (erros bars x20)", 
             color='navy', alpha=0.85, ms=5, capsize=3, elinewidth=1.5)

# Inseriamo il valore del Delta nella label del Fit
plt.plot(x_fit, f_fit, 
         label=f"Fit: $\Delta$ = {Delta_fit*1e3:.4f} ± {Delta_err*1e3:.4f} meV", 
         color='darkorange', alpha=0.9, lw=2.4)

# In alternativa, puoi stamparlo come testo fisso nel grafico:
# plt.text(0.05, 0.95, f"$\Delta$ = {Delta_fit*1e3:.3f} meV", 
#          transform=plt.gca().transAxes, verticalalignment='top', 
#          bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

plt.xlabel(r"Temperature (mK)")
plt.ylabel(r"$1/Q_i$")
#plt.title("Fit of Superconducting Gap")
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.savefig("SCgap_fit.png", dpi=300)
plt.savefig("SCgap_fit.pdf")
plt.show()