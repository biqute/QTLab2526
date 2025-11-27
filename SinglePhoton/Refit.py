import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# --------------------------------------------------------
# Load raw synthetic S21 data (with delay, environmental effects)
# --------------------------------------------------------
data = pd.read_csv("synthetic_S21.csv")

#mask = (data["frequency"] <= 5.004e9) & (data["frequency"] >= 4.995e9)
#data = data[mask]

freq = data["frequency"].values
S21_raw = data["Re(S21)"].values + 1j * data["Im(S21)"].values


# --------------------------------------------------------
# Probst Eq. (1): Complex S21 model for notch resonator
# --------------------------------------------------------
def S21_probst(f, a, alpha, Ql, Qc_mag, phi, fr, tau):
    """
    Full complex model of S21 Eq. (1) Probst et al.
    Inputs:
      f      : frequency array (Hz)
      a      : amplitude scale (>0)
      alpha  : global phase shift (rad)
      Ql     : loaded Q-factor
      Qc_mag : magnitude of complex coupling Qc
      phi    : angle of complex Qc
      fr     : resonant frequency (Hz)
      tau    : cable delay (seconds)
    """
    # complex coupling Qc
    Qc = Qc_mag * np.exp(-1j * phi)

    x = 2 * Ql * (f - fr) / fr       # dimensionless detuning

    # resonator response part (notch)
    notch = 1 - (Ql / Qc) / (1 + 1j * x)

    # environmental amplitude+phase and cable delay
    env = a * np.exp(1j * alpha) * np.exp(-2j * np.pi * f * tau)

    return env * notch


# --------------------------------------------------------
# Initial guesses (rough but sufficient)
# --------------------------------------------------------
a0      = 0.1
alpha0  = 2.18
Ql0     = 903
Qc_mag0 = 9974
phi0    = 0.3
fr0     = 5e9
tau0    = 5.03e-9  


#Parameters fitted
# tau = 5.0295 ns
# a = 0.1
# alpha = 2.18 rad, 125 degrees

# f_r = 5 GHz
# Q_loaded = 903
# Q_C = 9974
# Q_internal = 991
# phi = 17.15° or φ = 0.299 rad

p0 = [a0, alpha0, Ql0, Qc_mag0, phi0, fr0, tau0]

print("Initial guess:")
print("a =", a0)
print("alpha =", alpha0)
print("Ql =", Ql0)
print("Qc_mag =", Qc_mag0)
print("phi =", phi0)
print("fr0 (GHz) =", fr0/1e9)
print("tau0 (ns) =", tau0*1e9)


# --------------------------------------------------------
# Fit real and imaginary parts simultaneously
# --------------------------------------------------------
def fit_wrapper(f, a, alpha, Ql, Qc_mag, phi, fr, tau):
    model = S21_probst(f, a, alpha, Ql, Qc_mag, phi, fr, tau)
    return np.concatenate([model.real, model.imag])


S21_vec = np.concatenate([S21_raw.real, S21_raw.imag])

popt, pcov = curve_fit(
    fit_wrapper,
    freq,
    S21_vec,
    p0=p0,
    maxfev=20000
)

a_fit, alpha_fit, Ql_fit, Qc_mag_fit, phi_fit, fr_fit, tau_fit = popt

print("\n===== 7-Parameter Fit Results =====")
print(f"a       = {a_fit}")
print(f"alpha   = {alpha_fit}")
print(f"Q_l     = {Ql_fit}")
print(f"|Q_c|   = {Qc_mag_fit}")
print(f"phi     = {phi_fit}")
print(f"f_r     = {fr_fit}  Hz   ({fr_fit/1e9} GHz)")
print(f"tau     = {tau_fit*1e9} ns")


# --------------------------------------------------------
# Compute model and residuals
# --------------------------------------------------------
S21_fit = S21_probst(freq, *popt)

residuals = S21_raw - S21_fit
residual_mag = np.abs(residuals)


# --------------------------------------------------------
# Plot: S21 circle and residuals
# --------------------------------------------------------
plt.figure(figsize=(10,8))

# --- S21 circle (raw + fit) ---
plt.subplot(2,1,1)
plt.plot(S21_raw.real, S21_raw.imag, '.', ms=2, label="Raw data")
plt.plot(S21_fit.real, S21_fit.imag, 'r.', ms=2, label="Fit")

plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.title("S21 Complex Plane (Raw vs Fit)")
plt.grid(True)
plt.axis("equal")
plt.legend()

# --- Residuals ---
plt.subplot(2,1,2)
plt.plot(freq, residual_mag, '.k', ms=2)
plt.xlabel("Frequency (Hz)")
plt.ylabel("|Residual|")
plt.title("Fit Residuals: |S21_data − S21_fit|")
plt.grid(True)

plt.tight_layout()
plt.show()
