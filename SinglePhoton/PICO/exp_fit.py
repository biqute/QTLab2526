import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Leggi dati dal CSV
df = pd.read_csv("dati_fit.csv")

VDC = df['VDC (mV)'].values
VFD = df[' VFD (mV)(5000 points)'].values
err = df[' devstd_VFD (mV)    (8 ns )'].values

# Definisci modello esponenziale
def exp_model(x, A, B, C):
    return A * np.exp(B * x) + C

# Fit dei dati con barre di errore
popt, pcov = curve_fit(exp_model, VDC, VFD, sigma=err, absolute_sigma=True, p0=[-3500, 0.005, 1], maxfev = 10000)
A, B, C = popt
perr = np.sqrt(np.diag(pcov))  # errore sui parametri

print("Parametri del fit esponenziale:")
print(f"A = {A:.4f} ± {perr[0]:.4f}")
print(f"B = {B:.6f} ± {perr[1]:.6f}")
print(f"C = {C:.4f} ± {perr[2]:.4f}")

# Genera curva di fit per il plot
x_fit = np.linspace(min(VDC), max(VDC), 500)
y_fit = exp_model(x_fit, *popt)

# Plot dei dati con barre di errore e fit
plt.figure(figsize=(10,6))
plt.errorbar(VDC, VFD, yerr=err, fmt='o', capsize=5, markersize=5, ecolor='red', color='blue', label='Dati con errore')
plt.plot(x_fit, y_fit, 'g-', label='Fit esponenziale')
plt.xlabel('VDC (mV)')
plt.ylabel('VFD (mV)')
plt.title('Fit esponenziale dei dati della giunzione')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
