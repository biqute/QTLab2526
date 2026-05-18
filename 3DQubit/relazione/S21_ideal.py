import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Arc


def S21_notch_ideal(f, Ql, abs_Qc, phase_Qc, f0):
    mod_QC = abs_Qc
    phi = phase_Qc
    return  (1 - ((Ql/mod_QC) * np.exp(1j *phi))/(1 + 2j *Ql*(f/f0 -1)))


plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica",
    "axes.labelsize": 16,        # Dimensione label assi x e y
    "axes.titlesize": 18,        # Dimensione titolo
    "xtick.labelsize": 12,       # Dimensione tick x
    "ytick.labelsize": 12,       # Dimensione tick y
    "legend.fontsize": 14,       # Dimensione legenda
    "lines.linewidth": 2         # Spessore delle linee di default
})


fr   = 5.000e9      # resonance frequency (Hz)
Ql   = 1.0e4   # loaded Q (moderate sharpness)
Qc   = 2.0e4        # coupling Q magnitude
phi  = 0.5         # no impedance mismatch (ideal case)

d = Ql/Qc

f = np.linspace(4.99e9, 5.015e9, 10000)  # frequency range around resonance
S_21_plot = S21_notch_ideal(f, Ql, Qc, phi, fr)


plt.figure(figsize=(8, 6))

x, y = np.cos(phi), -np.sin(phi)

x_res =  S21_notch_ideal(fr, Ql, Qc, phi, fr).real
y_res =  S21_notch_ideal(fr, Ql, Qc, phi, fr).imag

# arc for angle (theta in degrees for Arc)
arc = Arc(
    (1, 0),
    width=0.6, height=0.7,
    angle=180,
    theta1=0,
    theta2=np.degrees(phi),
    color='black',

    lw=2
)

plt.text(0.8, -0.17, r"$d$", fontsize=15)
plt.text(0.6, -0.1, r"$\phi$", fontsize=15)
plt.annotate(r"$P$", (1, 0), xytext=(5, 5), textcoords="offset points", fontsize=15)
plt.annotate(r"$f_r$", (x_res, y_res), xytext=(-20, -20), textcoords="offset points", fontsize=15)
plt.gca().add_patch(arc)
plt.plot([x_res, 1], [y_res, 0], '--', lw=2, color='navy', alpha=0.85,)
plt.plot(S_21_plot.real, S_21_plot.imag, linestyle='-', color='navy', alpha=0.85)
plt.axvline(x=0, color='black', linewidth=1)
plt.axhline(y=0, color='black', linewidth=1)
plt.xlabel(r"$Q$")
plt.ylabel(r"$I$")
plt.title("Response of an ideal resonator")
plt.grid(True, linestyle='--', alpha=0.7)
plt.axis("equal")
plt.savefig("S21_ideal.pdf")
plt.show()