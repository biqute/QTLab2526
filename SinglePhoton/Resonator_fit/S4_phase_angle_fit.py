import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

#1)THE ONLY WAY TO PERFORM THIS FIT IS BY USING DATA FROM ONE SIDE OF DISCONTINUITY
#2)PHASE ANGLE FIT IS EXTREMELY SENSITIVE TO INITIAL VALUE OF RESONANT FREQUENCY. 
#For resonance at 5GHz it only works if initial value given is between 4.95 and 5.05 GHz

# -------------------------------------------------------
# Load delay-corrected data and circle parameters
# -------------------------------------------------------
data = pd.read_csv("S21_no_delay.csv")

# Keep only rows with frequency ≤ 5.005 GHz
mask = data["frequency"] <= 5.004e9
data = data[mask]

# Now extract frequency and S21
freq = data["frequency"].values
S21 = data["Re(S21)"].values + 1j * data["Im(S21)"].values

# If circle parameters are known already, define them here
# (otherwise load from file or pass them explicitly)
#x_c = float(input("Enter x_c from circle fit: "))
#y_c = float(input("Enter y_c from circle fit: "))
#r0  = float(input("Enter r_0 from circle fit: "))

x_c = -0.17481963335879977
y_c = -0.016849622752717452
r0 = 0.15652948290478952
#z = x_c + 1j*y_c
#argz = np.arcsin(y_c/r0)

# -------------------------------------------------------
# Shift S21 so circle is centered at origin
# -------------------------------------------------------
S21_shifted = S21 - (x_c + 1j*y_c)

# Compute phase (geometric angle on the resonator circle)
theta_shifted = np.angle(S21_shifted)

# -------------------------------------------------------
# Define fitting model (Eq. 12 from Probst)
# -------------------------------------------------------
def theta_model(f, theta0, Ql, fr):
    return theta0 + 2 * np.arctan(2 * Ql * (1 - f / fr))

# Initial guesses
theta0_guess = -0.94
Ql_guess = 1e3
fr_guess = 5e9

p0 = [theta0_guess, Ql_guess, fr_guess]

# -------------------------------------------------------
# Fit the phase to the model
# -------------------------------------------------------
popt, pcov = curve_fit(theta_model, freq, theta_shifted, p0=p0)

theta0_fit, Ql_fit, fr_fit = popt

print("\n===== Phase Fit Results (Probst Eq. 12) =====")
print(f"theta_0 = {theta0_fit*180/np.pi} degrees, {theta0_fit} rad")
#print(f"Arg(z) = {argz*180/np.pi} degrees, {argz} rad") #0.03 * np.pi
print(f"Phi should be = {0.03*180} degrees, {0.03 * np.pi} rad")
print(f"Q_loaded = {Ql_fit}")
print(f"f_r = {fr_fit/1e9} GHz")
print(f"Q_C = {0.5*Ql_fit/r0}")

# Compute fitted curve
theta_fit = theta_model(freq, *popt)

# -------------------------------------------------------
# Plot results
# -------------------------------------------------------
plt.figure(figsize=(8,6))
plt.plot(freq, theta_shifted, '.', ms=3, label="Shifted phase data")
plt.plot(freq, theta_fit, 'r-', lw=2, label="Fit: Probst Eq. (12)")

plt.xlabel("Frequency (Hz)")
plt.ylabel("Phase θ (rad)")
plt.title("Phase Fit to Probst Eq. (12)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

beta = theta0_fit + np.pi
P = x_c + r0*np.cos(beta) + 1j*(y_c + r0*np.sin(beta))
print(f"a = {np.abs(P)} as compared to {0.1}")
print(f"alpha = {np.angle(P)} rad as compared to {0.4 * np.pi}")
print(f"alpha = {np.angle(P)*180/np.pi} degrees as compared to {72} degrees")
#print(f"phi = {theta0_fit}")

#At this point we found
#1)tau - cable delay
#2)x_c, y_c, r - parameters of the circle
#3)theta_0, f_r and Q_l - from phase fit
#4)a, alpha and Q_C - scaling factor, global phase shift and couplig Q
