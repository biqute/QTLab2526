import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
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

filename = "qubit1/Data/RANGEpower_0.txt"

data = np.loadtxt(f'{filename}', skiprows=2)

# Rimuoviamo eventuali righe vuote o header lette come NaN

freq = data[:, 0]/1e9  # Frequenze in GHz
I = data[:, 1]   
Q = data[:, 2]     
signal = 20*np.log10(np.sqrt(I**2 + Q**2))  


plt.plot(freq, signal, label='Signal', color='navy', alpha=0.85)
plt.xlabel('Frequency (GHz)')
plt.ylabel('Transmission (dB)')
#plt.title(f'{filename} data', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(f"qubit1/Plots/FULLrange.pdf", dpi=300)
plt.show()