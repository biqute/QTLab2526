import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq
from scipy.optimize import curve_fit


def cos_func(x, A, freq, phi, B):
    return B + A*np.cos(2*np.pi*freq*x+phi)

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

# 1. Definisci i parametri temporali
fs = 10000             # Frequenza di campionamento (Hz)
n = len(data)           # Numero di punti

# 2. Calcola la FFT
fft_values = fft(data)
freqs = fftfreq(n, 1/fs)

# 3. Ottieni la magnitudo (ampiezza) e normalizza
# Usiamo solo la prima metà (frequenze positive)
mag = np.abs(fft_values[:n//2]) * (2.0 / n)
f_plot = freqs[:n//2]

# 4. Visualizza
plt.plot(f_plot, mag)
plt.xlabel("Frequenza (Hz)")
plt.ylabel("Ampiezza")
plt.show()
'''
time_us = data[:,0]/1e3
amp = data[:,1]
p0 = [-150, 1/(13), 0, 0]
# A: -500 to 0, freq: 0.01 to 1, phi: -π to π, B: -100 to 100
bounds = ([-160, 0.01, -0.01, -10], 
          [-150, 0.1, 0.01, 10])
popt, pcov = curve_fit(cos_func, time_us, amp, p0=p0, bounds=bounds)
A, f, phi, B = popt
print(f"Fitted parameters: A={A:.2f}, f={f:.2f} Hz, phi={phi:.2f} rad, B={B:.2f}")
x_fit = np.linspace(time_us.min(),time_us.max(),1000)
y_fit = cos_func(x_fit, *popt)
plt.plot(x_fit, y_fit, label = 'fit')
plt.plot(time_us, amp, label='Data', color='navy',  alpha=0.85,lw=1.5)
plt.xlabel(r"Time (us)")
plt.ylabel(r"Amplitude (a.u.)")
plt.grid(True, which='both', linestyle='--', alpha=0.6)
plt.legend()

plt.tight_layout()

#nome_grafico = "synth_plot.pdf"
#plt.savefig(f"data0_plots/{nome_grafico}")
plt.show()
'''