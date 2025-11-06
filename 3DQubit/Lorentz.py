from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

def lorentzian_power_tilt(f, A, f0, gamma, y0, m):
    """Lorentzian in power form + linear baseline tilt."""
    return y0 + m*(f - f0) + A / (1 + 4*(f - f0)**2 / gamma**2)

# your data
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])

f = frequencies
y = signal

# initial guesses
f0_guess = f[np.argmin(y)]
gamma_guess = (f.max() - f.min()) / 10
A_guess = y.max() - y.min()
y0_guess = np.median(np.r_[y[:max(10, len(y)//10)], y[-max(10, len(y)//10):]])  # robust baseline
m_guess  = (y[-1] - y[0]) / (f[-1] - f[0])  # baseline slope

p0 = [A_guess, f0_guess, gamma_guess, y0_guess, m_guess]

# fit
popt, pcov = curve_fit(lorentzian_power_tilt, f, y, p0=p0)
A_fit, f0_fit, gamma_fit, y0_fit, m_fit = popt

print("Fitted f0 =", f0_fit)
print("FWHM =", gamma_fit)

# ----- MINIMAL PLOT -----
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = lorentzian_power_tilt(f_fit, A_fit, f0_fit, gamma_fit, y0_fit, m_fit)

plt.plot(f, y, '.', label="data")
plt.plot(f_fit, y_fit, '-', label="Lorentzian + tilt")
plt.xlabel("frequency")
plt.ylabel("signal")
plt.legend()
plt.show()
