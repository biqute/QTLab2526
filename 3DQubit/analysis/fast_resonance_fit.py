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
save_as = "fast_resonance_plot"

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
perr = np.sqrt(np.diag(pcov)) # errors

# conversione in GHz
f0_fit_G = f0_fit/1e9 
gamma_fit_G = gamma_fit/1e9
quality_factor = f0_fit_G/gamma_fit_G

print(f"f0 (centro) = {f0_fit_G:.5g} GHz")
print(f"Gamma (FWHM) = {gamma_fit_G:.5g} GHz")
print(f"Quality factor = {quality_factor:.1g} GHz")

# === Creazione stringa per il plot === # 
text_str = (
    r"$f_0 = {:.4f} $ GHz" + "\n" +
    r"$\Delta f = {:.4f} $ GHz" + "\n" +
    r"$Q = {:.0f} $"
).format(f0_fit_G, gamma_fit_G, quality_factor)

# === Plot ===
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = lorentzian_power_tilt(f_fit, *popt)

fig, ax = plt.subplots()

#----Signal plot-----
ax.plot(f, y, '.', label="Dati (|S21|)")
ax.plot(f_fit, y_fit, '-', label="Fit Resonance")
ax.set_xlabel(r"$f[GHz]$")
ax.set_ylabel(r"$|S_{21}|$")
#ax_mag.grid(True, alpha=0.3)
ax.set_title("Magnitude")

# --- Aggiunta Legenda e Parametri --- # 
ax.legend(loc='upper right') # Mostra la legenda (Dati e Fit)
        
# Aggiunge un box con i parametri del fit
# transform=ax.transAxes usa coordinate relative (0,0 è basso-sx, 1,1 è alto-dx)
props = dict(boxstyle='round', facecolor='white', alpha=0.5, pad = 1.1)
ax.text(0.05, 0.95, text_str, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

save_as += ".pdf"
fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data0_plots/{save_as}")

plt.show()

