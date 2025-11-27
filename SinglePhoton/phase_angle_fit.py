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
#Data for scaled/shifted circle plots
data_full = pd.read_csv("S21_no_delay.csv")
freq_full = data_full["frequency"].values
S21_full = data_full["Re(S21)"].values + 1j * data_full["Im(S21)"].values

#Data for phase angle fit
data = pd.read_csv("S21_no_delay.csv")
mask = data["frequency"] <= 5.006e9
data = data[mask]
freq = data["frequency"].values
S21 = data["Re(S21)"].values + 1j * data["Im(S21)"].values

# If circle parameters are known already, define them here
# (otherwise load from file or pass them explicitly)
#x_c = float(input("Enter x_c from circle fit: "))
#y_c = float(input("Enter y_c from circle fit: "))
#r0  = float(input("Enter r_0 from circle fit: "))
x_c = -0.021780511582819996
y_c = 0.05455076885607019
r0 = 0.04527254564185787
#z = x_c + 1j*y_c
#argz = np.arcsin(y_c/r0)

# -------------------------------------------------------
# Shift S21 so circle is centered at origin
# -------------------------------------------------------
S21_shifted_full = S21_full - (x_c + 1j*y_c)
S21_shifted = S21 - (x_c + 1j*y_c)

# Compute phase (geometric angle on the resonator circle)
theta_shifted = np.angle(S21_shifted)

# -------------------------------------------------------
# Define fitting model (Eq. 12 from Probst)
# -------------------------------------------------------
def theta_model(f, theta0, Ql, fr):
    return theta0 + 2 * np.arctan(2 * Ql * (1 - f / fr))

# Initial guesses
theta0_guess = -1.5
Ql_guess = 1e3
fr_guess = 5e9

p0 = [theta0_guess, Ql_guess, fr_guess]

# -------------------------------------------------------
# Fit the phase to the model
# -------------------------------------------------------
popt, pcov = curve_fit(theta_model, freq, theta_shifted, p0=p0)

theta0_fit, Ql_fit, fr_fit = popt
QC = 0.5*Ql_fit/r0
print("\n===== Phase Fit Results (Probst Eq. 12) =====")
print(f"theta_0 = {theta0_fit*180/np.pi} degrees, {theta0_fit} rad")
#print(f"Arg(z) = {argz*180/np.pi} degrees, {argz} rad") #0.03 * np.pi
#print(f"Phi should be = {0.03*180} degrees, {0.03 * np.pi} rad")
print(f"Q_loaded = {Ql_fit}")
print(f"f_r = {fr_fit/1e9} GHz")
print(f"Q_C = {0.5*Ql_fit/r0}")
print(f"Q_internal =  {(QC*Ql_fit)/(QC-Ql_fit)}")

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
print(f"P_angle = {np.angle(P)} rad, {np.angle(P)*180/np.pi} degrees")
a = np.abs(P)
S21_scaled = S21_shifted_full/a

plt.figure(figsize=(6,6))
plt.plot(S21_scaled.real, S21_scaled.imag, '.', ms=2, label='scaled')
plt.plot(S21_shifted_full.real, S21_shifted_full.imag, '.', label='only shifted')
plt.title("S21 shifted to the center (Complex Plane)")
plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.grid(True)
plt.axis('equal')
plt.legend()
plt.show()

#At this point we found
#1)tau - cable delay
#2)x_c, y_c, r - parameters of the circle
#3)theta_0, f_r and Q_l - from phase fit
#4)a, alpha and Q_C - scaling factor, global phase shift and couplig Q

#Parameters fitted
# tau = 5.0295 ns
# f_r = 5 GHz
# Q_loaded = 903
# Q_C = 9974
# a = 0.1
# P_angle = 2.18 rad, 125 degrees

# theta_0 = -38.10147884251284 degrees, -0.664996255680807 rad
# x_c = -0.021780511582819996
# y_c = 0.05455076885607019
# r_0 = 0.04527254564185787
