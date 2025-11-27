import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

#HERE I PLOT CIRCLES BEFORE AND AFTER SHIFT

# -------------------------------------------------------
# Load delay-corrected data and circle parameters
# -------------------------------------------------------
data = pd.read_csv("S21_no_delay.csv")

# Keep only rows with frequency ≤ 5.005 GHz
#mask = data["frequency"] <= 5.004e9
#data = data[mask]

# Now extract frequency and S21
freq = data["frequency"].values
S21 = data["Re(S21)"].values + 1j * data["Im(S21)"].values

theta = np.angle(S21)

# If circle parameters are known already, define them here
# (otherwise load from file or pass them explicitly)
x_c = -0.021780511582819996
y_c = 0.05455076885607019
r_0 = 0.04527254564185787

a = 0.1
P_angle = 2.18
S21_scaled = S21/a

# -------------------------------------------------------
# Shift S21 so circle is centered at origin
# -------------------------------------------------------
S21_shifted = S21 - (x_c + 1j*y_c)

# Compute phase (geometric angle on the resonator circle)
theta_shifted = np.angle(S21_shifted)



# -------------------------------------------------------
# Plot results
# -------------------------------------------------------
plt.figure(figsize=(6,6))
plt.plot(S21_scaled.real, S21_scaled.imag, '.', ms=2, label='scaled')
plt.plot(S21.real, S21.imag, '.', label='original')
plt.title("S21 shifted to the center (Complex Plane)")
plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.grid(True)
plt.axis('equal')
plt.legend()
plt.show()

plt.figure(figsize=(8,6))
plt.plot(freq, theta, '.', ms=3, label="Original phase data")
plt.plot(freq, theta_shifted, '.', lw=2, label="Shifted phase data")

plt.xlabel("Frequency (Hz)")
plt.ylabel("Phase θ (rad)")
plt.title("Phase data before and after shifting circle")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()