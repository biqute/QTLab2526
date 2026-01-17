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
data_file = "misura_S21"
save_as = "Fit_Lorentz"

# Assumi che il file ../data/misura_S21.txt contenga: freq, real, imag
data = np.loadtxt("../data/"+data_file + ".txt", delimiter="\t")

# Separa le colonne
f = data[:, 0]              # Frequenza
real = data[:, 1]
imag = data[:, 2]
phase = np.atan(imag/real)

# Calcola modulo o potenza
# Se il tuo segnale è in dB, puoi fare:
# y = 20 * np.log10(np.sqrt(real**2 + imag**2))
# Se invece vuoi lavorare in potenza lineare:
y = np.sqrt(real**2 + imag**2)

# === Stime iniziali ===
f0_guess = f[np.argmax(y)]          # picco massimo (o np.argmin se è una "dip")
gamma_guess = (f.max() - f.min()) / 10
A_guess = y.max() - y.min()
y0_guess = np.median(np.r_[y[:max(10, len(y)//10)], y[-max(10, len(y)//10):]])
m_guess  = (y[-1] - y[0]) / (f[-1] - f[0])

p0 = [A_guess, f0_guess, gamma_guess, y0_guess, m_guess]

# === Fit ===
popt, pcov = curve_fit(lorentzian_power_tilt, f, y, p0=p0)
A_fit, f0_fit, gamma_fit, y0_fit, m_fit = popt

print(f"f0 (centro) = {f0_fit:.6g}")
print(f"Gamma (FWHM) = {gamma_fit:.6g}")

# === Plot ===
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = lorentzian_power_tilt(f_fit, *popt)

fig = plt.figure(figsize=(10, 6), constrained_layout=True) # --Layout: big left (IQ), right (mag, phase)

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
ax_iq.plot(real, imag, marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax_iq.set_aspect('equal', 'box')
ax_iq.axhline(0, color='gray', linewidth=0.8)   # real axis (horizontal)
ax_iq.axvline(0, color='gray', linewidth=0.8)   # imaginary axis (vertical)
ax_iq.set_xlabel(r"$\Re\{S_{21}\}$")          
ax_iq.set_ylabel(r"$\Im\{S_{21}\}$")
#ax_iq.plot([1], [0], "ro", ms = 8, label = "P(1,0)") 
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

#----Signal plot-----
ax_mag.plot(f/1e9, y, '.', label="Dati (|S21|)")
ax_mag.plot(f_fit/1e9, y_fit, '-', label="Fit Lorentz + tilt")
ax_mag.set_xlabel(r"$f\,[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

#----Phase plot-------
ax_phase.plot(f/1e9, phase, '-', lw=1)
ax_phase.set_xlabel(r"$f\,[GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")
ax_phase.legend(loc ="best")
            
save_as += ".pdf"
fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data0_plots/{save_as}")

plt.show()

