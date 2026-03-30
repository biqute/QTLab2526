import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# -------------------------------------------------------
# Load synthetic data
# -------------------------------------------------------
data = pd.read_csv(r"C:\Users\kid\labQT\Lab2025\Single photon\QTLab2526\SinglePhoton\NC_S21_large_int.csv")

#mask = (data["frequency"] >= 5.05e9) & (data["frequency"] <= 5.13e9)
#mask = (data["frequency"] <= 4.96e9) | (data["frequency"] >= 5.03e9)
#mask = (data["frequency"] <= 4.945e9)
#mask = (data["frequency"] >= 5.13e9)
#data = data[mask]

freq = data["frequency"].values
phase = data["phase"].values
S21 = data["Re(S21)"].values + 1j * data["Im(S21)"].values

# -------------------------------------------------------
# Fit phase vs frequency to a linear function
# -------------------------------------------------------
def linear(f, m, b):
    return -2 * np.pi*m * f + b

popt, pcov = curve_fit(linear, freq, phase)
m_fit, b_fit = popt

print("Parameter to use in exp for removal of cable delay =", 2 * np.pi*m_fit)
print("Fitted intercept b =", b_fit)

# -------------------------------------------------------
# Extract cable delay
# m = -2*pi*tau  =>  tau = -m/(2*pi)
# -------------------------------------------------------
tau_estimated = m_fit 
print(f"Estimated cable delay tau = {tau_estimated * 1e9:.4f} ns")

# -------------------------------------------------------
# Remove cable delay
# S21_corrected = S21 * exp(+2j*pi*f*tau_estimated)
# -------------------------------------------------------
S21_corrected = S21 * np.exp(2j * np.pi * freq * tau_estimated)

# Compute magnitude and phase for corrected data
amp_corr = np.abs(S21_corrected)
phase_corr = np.angle(S21_corrected)


# -------------------------------------------------------
# Diagnostic plots
# -------------------------------------------------------
plt.figure(figsize=(12,8))

# ---- 1. Phase vs Frequency (Original)
plt.subplot(2,2,1)
plt.plot(freq, phase, '.', ms=2, label='Original')
plt.plot(freq, linear(freq, *popt), 'r-', label='Linear Fit')
plt.title("Phase vs Frequency (with Cable Delay)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Phase (rad)")
plt.grid(True)
plt.legend()

# ---- 2. Phase vs Frequency (Corrected)
plt.subplot(2,2,2)
plt.plot(freq, phase_corr, '.', ms=2)
plt.title("Phase vs Frequency (Delay Removed)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Phase (rad)")
plt.grid(True)

# ---- 3. Complex Plane With Delay
plt.subplot(2,2,3)
plt.plot(S21.real, S21.imag, '.', ms=2)
plt.title("Complex Plane: S21 with Cable Delay")
plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.grid(True)
plt.axis('equal')

# ---- 4. Complex Plane Without Delay
plt.subplot(2,2,4)
plt.plot(S21_corrected.real, S21_corrected.imag, '.', ms=2, label="Corrected")
plt.title("Complex Plane: S21 after Delay Removal")
plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.grid(True)
plt.axis('equal')

plt.tight_layout()
plt.show()

#plt.savefig("Cable_delay_fit")

#Estimated cable delay tau = 5.0295 ns