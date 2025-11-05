import numpy as np
from scipy import optimize
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from circle_fit import CircleFitter

TAU = 4.000467548463284e-05 #From data.npz

# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

#---Fit functions------
def atan_model(x, A, B, C, D):
    return A * np.arctan(B * x + C) + D

# ---------------- Load data ----------------
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])

#------Finding Resonance-----
idx = np.argmin(signal)


S21 = signal * np.exp(1j * phase)#*np.exp(-1j* 2*np.pi * TAU* frequencies)
real_S21 = S21.real
imag_S21 = S21.imag

# ---------------- Circle fit via CircleFitter ----------------
fitter = CircleFitter()
x_c, y_c, r_0 = fitter.fit_from_complex(S21)


# Phase after removing cable delay)
phase_corrected = np.arctan2(imag_S21, real_S21)


# ---- Plot ----
theta = np.linspace(0, 2*np.pi, 400)
xcirc = x_c + r_0 * np.cos(theta)
ycirc = y_c + r_0 * np.sin(theta)

# --Layout: big left (IQ), right (mag, phase) ---
fig = plt.figure(figsize=(10, 6), constrained_layout=True)

gs = GridSpec(
    2, 2, figure=fig,
    width_ratios=[2.7, 1.3],  # big left vs small right
    height_ratios=[1, 1],
    wspace=0.01,               # gap between left and right
    hspace=0.05,               # vertical spacing between small plots
    left=1.2,                 # left margin
    right=1.5,                 # right margin — increase for more border space
    bottom=0.1, top=0.92       # vertical margins
)

ax_iq    = fig.add_subplot(gs[:, 0])  # spans both rows on the left
ax_mag   = fig.add_subplot(gs[0, 1])  # top-right
ax_phase = fig.add_subplot(gs[1, 1])  # bottom-right

# ---- IQ plot ----
ax_iq.plot(real_S21[::50], imag_S21[::50], '.', ms=1.5, label='Data')
ax_iq.plot(xcirc, ycirc, '-', lw=2, label='Fitted circle')
ax_iq.set_aspect('equal', 'box')
ax_iq.set_xlabel(r"$\Re\{S_{21}\}$")          
ax_iq.set_ylabel(r"$\Im\{S_{21}\}$")          
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

ax_mag.plot(frequencies/1e9, signal, '-', lw=1)
ax_mag.set_xlabel(r"$f[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

ax_phase.plot(frequencies/1e9, phase, '-', lw=1)
ax_phase.set_xlabel(r"$f [GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")

plt.show()
