from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec 

'''
Lorentzian fit with power and linear tilt for cavity resonance data. 
The model includes a Lorentzian term to capture the resonance, 
a linear term to account for any background slope, and a constant offset. 
The script reads the data from a specified file, performs the fit, 
and plots the results in both the IQ plane and as magnitude and phase vs frequency. 
The fitted parameters are printed to the console, 
and the resulting plot is saved as a PDF.
'''

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica",
    "axes.labelsize": 16,        # Dimensione label assi x e y
    "axes.titlesize": 18,        # Dimensione titolo
    "xtick.labelsize": 14,       # Dimensione tick x
    "ytick.labelsize": 14,       # Dimensione tick y
    "legend.fontsize": 14,       # Dimensione legenda
    "lines.linewidth": 2         # Spessore delle linee di default
})

def skewed_lorentz(f, f0, Q, A, B, y0, m):
    """
    Modello per un dip di risonanza asimmetrico.
    f: Frequenza (in GHz)
    f0: Frequenza di risonanza centrale
    Q: Fattore di qualità
    A: Profondità del dip (componente Lorentziana simmetrica)
    B: Fattore di asimmetria (componente dispersiva)
    y0: Livello di background (offset)
    m: Pendenza del background (slope)
    """
    x = f - f0
    bkg = y0 + m*x
    signal = (A + B*x)/(1+4*Q**2*(x/f0)**2)

    return bkg + signal


# === Lettura dati ===
data_file = "../qubit0/Data/ZOOMpower_0.txt" 
save_as = "../qubit0/Plots/LorentzFit_0dBm"

# Assumi che il file contenga: freq, real, imag
data = np.loadtxt(data_file, delimiter="\t")
# Separa le colonne
f = data[:, 0]/1e9  # Converti a GHz              
real = data[:, 1]
imag = data[:, 2]
'''
x_min = f.min()+0.05
x_max = f.max()-0.05
mask = (f > x_min) & (f < x_max)
f = f[mask]
real = real[mask]
imag = imag[mask]
'''
phase = np.unwrap(np.atan2(imag, real))

# Calcola modulo o potenza
# Se il tuo segnale è in dB, puoi fare:
# y = 20 * np.log10(np.sqrt(real**2 + imag**2))
# Se invece vuoi lavorare in potenza lineare:
y = real**2 + imag**2

''' FIT LORENTZ ASIMMETRICA '''

"""
    Modello per un dip di risonanza asimmetrico.
    f: Frequenza (in GHz)
    f0: Frequenza di risonanza centrale
    Q: Fattore di qualità
    A: Profondità del dip (componente Lorentziana simmetrica)
    B: Fattore di asimmetria (componente dispersiva)
    y0: Livello di background (offset)
    m: Pendenza del background (slope)
    """

p0 = [f[np.argmax(y)], # f0 guess
      1e3, # Q guess
      y.max() - y.min(), # A guess
      0, # B guess (nessuna asimmetria iniziale)
      np.mean(y[:10]), # y0 guess
      0.01] # m guess

lower_bounds = [f.min(), 0, 0, -np.inf, 0, -1]
upper_bounds = [f.max(), 1e5, np.inf, np.inf, 1, 1]

popt, pcov = curve_fit(skewed_lorentz, f, y, p0=p0, bounds=(lower_bounds, upper_bounds))
print("f0 = {:.3f} GHz".format(popt[0]))
print("Q = {:.0f}".format(popt[1]))
print("A = {:.6g} GHz".format(popt[2]))
print("B = {:.6g}".format(popt[3]))
print("y0 = {:.6g}".format(popt[4]))
print("m = {:.6g}".format(popt[5]))
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = skewed_lorentz(f_fit, *popt)

f0_val = popt[0]
Q_val = popt[1]
#----Signal plot-----
plt.plot(f, y, '.', label="Data", color = 'navy', alpha = 0.85)
plt.plot(f_fit, y_fit, '-', label='Fit', color = 'darkorange', alpha = 0.9, lw = 2.4)
plt.xlabel(r"Frequency (GHz)")
plt.ylabel(r"$|S_{21}|^2$")
plt.grid(True, alpha=0.3)
#plt.legend(loc="best", fontsize=14)
#plt.title("Magnitude")
testo = f"$f_0 = {f0_val:.3f}$ GHz\n$Q = {Q_val:.0f}$"

# Posiziona il testo (ad es. coordinate relative: x=0.05, y=0.05 è in basso a sinistra)
plt.annotate(testo, xy=(0.05, 0.9), xycoords='axes fraction',
             fontsize=16, verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))
save_as += ".pdf"
plt.savefig(save_as, bbox_inches="tight")
print(f"Grafico salvato in {save_as}")

plt.show()

