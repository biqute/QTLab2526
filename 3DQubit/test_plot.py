import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq
from scipy.optimize import curve_fit


def sin_func(x, A, omega, phi, B):
    return B + A*np.sin(omega*x+phi)

########## IMPOSTAZIONI GRAFICHE (Aesthetic Improvements) #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica",
    "axes.labelsize": 14,        # Dimensione label assi x e y
    "axes.titlesize": 18,        # Dimensione titolo
    "xtick.labelsize": 12,       # Dimensione tick x
    "ytick.labelsize": 12,       # Dimensione tick y
    "legend.fontsize": 14,       # Dimensione legenda
    "lines.linewidth": 2         # Spessore delle linee di default
})

# 1. Caricamento dati 
data = np.loadtxt("data/acquisizione.txt")

f = data[:,0]/1e9
amp = data[:,1]

popt, pcov = curve_fit(sin_func, f, amp)
print(popt)
x_fit = np.linspace(f.min(),f.max(),1000)
y_fit = sin_func(x_fit, *popt)
plt.plot(x_fit, y_fit)
plt.plot(f, amp, label='Data Synth', color='navy',  alpha=0.85,lw=1.5)
plt.xlabel(r"Frequency (GHz)")
plt.ylabel(r"Transmission (dBm)")
plt.grid(True, which='both', linestyle='--', alpha=0.6)
#plt.legend()

plt.tight_layout()

#nome_grafico = "synth_plot.pdf"
#plt.savefig(f"data0_plots/{nome_grafico}")
plt.show()