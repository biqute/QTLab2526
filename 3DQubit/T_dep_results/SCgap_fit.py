import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import i0, k0

#def model(T, a, b, Delta):
#    # Boltzmann constant in eV/mK: (J/K) * (1/ (J/eV)) * (1 K / 1000 mK)
#    k_B = 8.617333e-5 / 1000  
#    return a + b * np.exp(-Delta / (k_B * T))

# --- COSTANTI FISICHE ---
k_B = 8.617333262145e-5  # Costante di Boltzmann (eV/K)
h = 4.135667696e-15      # Costante di Planck (eV s)
 
def inverse_Qi_model(T_mK, inv_Qi_0, alpha, Delta_eV, f_0):
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
data = np.loadtxt("revQ_vs_Temperature.txt")
temp = data[:,0]
revQ = data[:,1]

p0 = [0.001, 1000, 0.001]

# === Fit ===
# Aggiungiamo i bounds per evitare l'overflow (Delta deve essere positivo)
popt, pcov = curve_fit(model, temp, revQ, p0=p0)
a_fit, b_fit, Delta_fit = popt

# Calcolo dell'errore (opzionale ma utile)
perr = np.sqrt(np.diag(pcov))
Delta_err = perr[2]

print(f"Superconducting Gap = {Delta_fit*1e3:.4f} meV")

# Prepara i dati per il plot del fit
x_fit = np.linspace(np.min(temp), np.max(temp), 100)
f_fit = model(x_fit, a_fit, b_fit, Delta_fit)

plt.figure(figsize=(8, 6))
plt.plot(temp, revQ, label="Data", marker="o", linestyle="", color="black", alpha=0.6)

# Inseriamo il valore del Delta nella label del Fit
plt.plot(x_fit, f_fit, 
         label=f"Fit: $\Delta$ = {Delta_fit*1e3:.3f} ± {Delta_err*1e3:.3f} meV", 
         linewidth=2, color="red")

# In alternativa, puoi stamparlo come testo fisso nel grafico:
# plt.text(0.05, 0.95, f"$\Delta$ = {Delta_fit*1e3:.3f} meV", 
#          transform=plt.gca().transAxes, verticalalignment='top', 
#          bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

plt.xlabel("Temperature (mK)")
plt.ylabel("1/Q")
plt.title("Fit of Superconducting Gap")
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.savefig("SCgap_fit.png", dpi=300)
plt.show()