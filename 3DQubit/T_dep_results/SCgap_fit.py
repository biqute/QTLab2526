import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def model(T, a, b, Delta):
    # Boltzmann constant in eV/mK: (J/K) * (1/ (J/eV)) * (1 K / 1000 mK)
    k_B = 8.617333e-5 / 1000  
    return a + b * np.exp(-Delta / (k_B * T))

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