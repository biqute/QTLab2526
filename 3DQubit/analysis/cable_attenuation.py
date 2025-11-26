from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec 

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

def lorentzian_power_tilt(f, A, f0, gamma, y0, m):
    """Lorentziana in potenza + pendenza lineare."""
    return y0 + m*(f - f0) + A / (1 + 4*(f - f0)**2 / gamma**2)

# === Lettura dati ===
cable_name = "long_1"
data_file = "data_cable_" + cable_name
save_as = "cable_att_fit_" + cable_name

# Assumi che il file ../data/misura_S21.txt contenga: freq, real, imag
data = np.loadtxt("../data/"+data_file + ".txt", delimiter="\t")

# Separa le colonne
f = data[:, 0]              # Frequenza
real = data[:, 1]
imag = data[:, 2]

# Calcola modulo o potenza
# Se il tuo segnale è in dB, puoi fare:
# Se invece vuoi lavorare in potenza lineare:
amp = 10*np.log10(real**2+imag**2)

# === Stime iniziali ===


# === Fit ===
#popt, pcov = curve_fit(lorentzian_power_tilt, f, y, p0=p0)


# === Plot ===
#f_fit = np.linspace(f.min(), f.max(), 2000)
#y_fit = lorentzian_power_tilt(f_fit, *popt)


fig = plt.figure(figsize=(10, 6), constrained_layout=True) # --Layout: non smooth left , smooth right 

gs = GridSpec(
    1, 1, figure=fig,
    #width_ratios=[2.7, 1.3],  # big left vs small right
    height_ratios=[1, 1],
    wspace=0.01,               # gap between left and right
    #hspace=0.05,               # vertical spacing between small plots
    left=1.2,                 # left margin
    right=1.5,                 # right margin — increase for more border space
    bottom=0.1, top=0.92       # vertical margins
)

ax    = fig.add_subplot(gs[0])  # left
ax_smooth   = fig.add_subplot(gs[1])  # right

# ---- non smooth plot ----
ax.plot(real, imag, marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax.set_aspect('equal', 'box')
ax.axhline(0, color='gray', linewidth=0.8)   # real axis (horizontal)
ax.axvline(0, color='gray', linewidth=0.8)   # imaginary axis (vertical)
ax.set_xlabel(r"$\Re\{S_{21}\}$")          
ax.set_ylabel(r"$\Im\{S_{21}\}$")
ax.legend(loc='best')
ax.set_title(r"I-Q Plot")

#----smooth plot-----
ax_mag.plot(f, y, '.', label="Dati (|S21|)")
ax_mag.plot(f_fit, y_fit, '-', label="Fit Lorentz + tilt")
ax_mag.set_xlabel(r"$f[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

#----Phase plot-------
ax_phase.plot(f, phase, '-', lw=1)
ax_phase.set_xlabel(r"$f [GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")
ax_phase.legend(loc ="best")
            
save_as += ".pdf"
fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data/{save_as}")

