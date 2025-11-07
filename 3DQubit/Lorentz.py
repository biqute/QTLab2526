from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

# --- Fano notch (asymmetric) + linear baseline tilt ---
def fano_notch_tilt(f, A, f0, gamma, q, y0, m):
    """
    Asymmetric (Fano) dip:
      x = 2*(f - f0)/gamma
      y = y0 + m*(f - f0) - A * (q + x)^2 / (1 + x^2)
    q controls the asymmetry (q>0 → right-side tail for a dip).
    """
    x = 2*(f - f0)/gamma
    return y0 + m*(f - f0) - A * ((q + x)**2) / (1.0 + x**2)

# your data
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])

f = frequencies
y = signal

# initial guesses (minimal)
idx = np.argmin(y)
f0_guess = f[idx]
gamma_guess = (f.max() - f.min()) / 10
y0_guess = np.median(np.r_[y[:max(10, len(y)//10)], y[-max(10, len(y)//10):]])  # robust baseline
A_guess = max(y0_guess - y[idx], 1e-12)   # dip depth
m_guess  = (y[-1] - y[0]) / (f[-1] - f[0])  # baseline slope
q_guess = 0.5   # small positive asymmetry (bump on the right)

p0 = [A_guess, f0_guess, gamma_guess, q_guess, y0_guess, m_guess]

# fit
popt, pcov = curve_fit(fano_notch_tilt, f, y, p0=p0)
A_fit, f0_fit, gamma_fit, q_fit, y0_fit, m_fit = popt

print("Fitted f0        =", f0_fit)
print("FWHM-like gamma  =", gamma_fit)
print("Fano q (asymmetry) =", q_fit)

# ----- MINIMAL PLOT -----
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = fano_notch_tilt(f_fit, A_fit, f0_fit, gamma_fit, q_fit, y0_fit, m_fit)

plt.plot(f, y, '.', label="data")
plt.plot(f_fit, y_fit, '-', label="Fano + tilt")
plt.xlabel("frequency")
plt.ylabel("signal")
plt.legend()
plt.show()
