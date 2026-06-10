import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy import optimize
from scipy.optimize import curve_fit 
import sys
sys.path.append("/")

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

def line(x, m, q):
    return m * x + q

def guess_delay(f_data, z_data):
    phase2 = np.unwrap(np.angle(z_data))
    gradient, intercept, r_value, p_value, std_err = stats.linregress(f_data, phase2)
    return gradient * (-1) / (np.pi * 2.)

def remove_cable_delay(f_data, z_data, delay):
    return z_data * np.exp(+2j * np.pi * f_data * delay)

def fit_from_complex(z_data):
    def calc_R(xc, yc):
        return np.sqrt((z_data.real - xc)**2 + (z_data.imag - yc)**2)
    def cost(c):
        Ri = calc_R(*c)
        return Ri - Ri.mean()
    x_m, y_m = z_data.real.mean(), z_data.imag.mean()
    result = optimize.least_squares(cost, [x_m, y_m])
    xc, yc = result.x
    r0 = calc_R(xc, yc).mean()
    return xc, yc, r0

def fit_delay(f_data, z_data, delay=0.):
    def residuals(p, x, y):
        phasedelay = p
        z_data_temp = y * np.exp(1j * (2. * np.pi * phasedelay * x))
        xc, yc, r0 = fit_from_complex(z_data_temp)
        err = np.sqrt((z_data_temp.real - xc)**2 + (z_data_temp.imag - yc)**2) - r0
        return err
    p_final = optimize.leastsq(residuals, delay, args=(f_data, z_data),
                                maxfev=10000, ftol=1e-15, xtol=1e-15)
    return p_final[0][0]


n_misura = "2"
save_as = "fit_0dBm" + n_misura

data = np.loadtxt("qubit1/Data/ZOOMpower_0.txt")

# ← Frequenze in Hz per tau consistente con le unità fisiche
frequencies_Hz = data[:, 0]
frequencies_GHz = data[:, 0] / 1e9

real_S21 = data[:, 1]
imag_S21 = data[:, 2]

# Costruisci S21 direttamente (senza ricomporre modulo+fase)
S21 = real_S21 + 1j * imag_S21
phase = np.unwrap(np.angle(S21))

# Invece di:
TAU = guess_delay(frequencies_Hz, S21)

# Fai così: fit lineare solo sulle ali (escludi il 40% centrale)
n = len(frequencies_Hz)
margin = int(0.30 * n)
mask = np.ones(n, dtype=bool)

# Trova il centro della risonanza (minimo del modulo)
res_idx = np.argmin(np.abs(S21))
mask[max(0, res_idx - margin): min(n, res_idx + margin)] = False

phase_uw = np.unwrap(np.angle(S21))
from scipy import stats
gradient, intercept, _, _, _ = stats.linregress(frequencies_Hz[mask], phase_uw[mask])
TAU = gradient * (-1.) / (np.pi * 2.)
print("TAU dalle ali:", TAU)

# Poi fit_delay come raffinamento
S21_cal = remove_cable_delay(frequencies_Hz, S21, TAU)


# --- Plot 2: I vs Q raw e cable delay rimosso ---
plt.figure(figsize=(7, 7))
plt.plot(S21.real, S21.imag,
         color='red', marker='.', linestyle='None', markersize=1,
         label=r'Raw $S_{21}$')
plt.plot(S21_cal.real, S21_cal.imag,
         color='blue', marker='.', linestyle='None', markersize=1,
         label=r'$S_{21}$ cable delay rimosso')
plt.title(r'Piano complesso $I$-$Q$', fontsize=14)
plt.xlabel(r'$I$ (Re$[S_{21}]$)', fontsize=12)
plt.ylabel(r'$Q$ (Im$[S_{21}]$)', fontsize=12)
plt.legend(fontsize=11)
plt.axis('equal')
plt.grid(True)
plt.tight_layout()

plt.show()