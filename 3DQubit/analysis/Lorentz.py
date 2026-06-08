import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from iminuit import Minuit
from iminuit.cost import LeastSquares

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
    signal = (A + B*x)/(1 + 4*Q**2*(x/f0)**2)

    return bkg + signal


# === Lettura dati ===
data_file = "../data/cavity_7.29GHz_corretta_2cavi.txt" 
save_as = "../cavity_Tamb/Tamb_plots/cavity_0_fit"

# Assumi che il file contenga: freq, real, imag
data = np.loadtxt(data_file, delimiter="\t")

# Separa le colonne
f = data[:, 0] / 1e9  # Converti a GHz              
real = data[:, 1]
imag = data[:, 2]

phase = np.unwrap(np.atan2(imag, real))

# Calcola potenza (lineare)
y = real**2 + imag**2


''' FIT LORENTZ ASIMMETRICA CON IMINUIT '''

# Costruiamo la funzione di costo LeastSquares. 
# Dato che non abbiamo un array di errori esplicito (sigma), passiamo 1.0 (peso uniforme).
cost_func = LeastSquares(f, y, 1.0, skewed_lorentz)

# Definiamo i valori iniziali (guess)
f0_guess = f[np.argmax(y)]
Q_guess  = 1e3
A_guess  = y.max() - y.min()
B_guess  = 0.0
y0_guess = np.mean(y[:10])
m_guess  = 0.01

# Inizializziamo l'oggetto Minuit con la funzione di costo e i valori iniziali
m = Minuit(cost_func, f0=f0_guess, Q=Q_guess, A=A_guess, B=B_guess, y0=y0_guess, m=m_guess)

# Impostiamo i limiti per ogni parametro (in iminuit `None` significa senza limite)
m.limits["f0"] = (f.min(), f.max())
m.limits["Q"]  = (0, 1e5)
m.limits["A"]  = (0, None)
m.limits["B"]  = (None, None)
m.limits["y0"] = (0, 1)
m.limits["m"]  = (-1, 1)

# === ESECUZIONE DEL FIT ===
m.migrad()  # Ottimizzazione dei parametri
m.hesse()   # Stima degli errori sui parametri

# Stampiamo il resoconto del fit per comodità (formattazione testuale integrata in iminuit)
print(m)

# Recuperiamo i parametri ottimizzati
popt = m.values
f0_val = popt["f0"]
Q_val = popt["Q"]

print("\n--- Risultati del Fit ---")
print("f0 = {:.3f} GHz".format(f0_val))
print("Q  = {:.0f}".format(Q_val))
print("A  = {:.6g}".format(popt["A"]))
print("B  = {:.6g}".format(popt["B"]))
print("y0 = {:.6g}".format(popt["y0"]))
print("m  = {:.6g}".format(popt["m"]))

# Creiamo le curve per il plot del fit usando i parametri ottimizzati
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = skewed_lorentz(f_fit, *popt)


# === PLOT DEL SEGNALE ===
plt.plot(f, y, '.', label="Data", color='navy', alpha=0.85)
plt.plot(f_fit, y_fit, '-', label='Fit', color='darkorange', alpha=0.9, lw=2.4)

plt.xlabel(r"Frequency (GHz)")
plt.ylabel(r"$|S_{21}|^2$")
plt.grid(True, alpha=0.3)

testo = f"$f_0 = {f0_val:.3f}$ GHz\n$Q = {Q_val:.0f}$"

# Posiziona il box di testo
plt.annotate(testo, xy=(0.05, 0.9), xycoords='axes fraction',
             fontsize=16, verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

save_as += ".pdf"
plt.savefig(save_as, bbox_inches="tight")
print(f"Grafico salvato in {save_as}")

plt.show()