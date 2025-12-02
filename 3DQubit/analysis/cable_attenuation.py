from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec 

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

#def attenuation_fit(x, a, b, c, d, phase, offset):
    #return a * np.exp(-b * x) + c*np.sin(d*x+phase) + offset

def attenuation_fit(x, a, b, c, phase, offset):
    return a * x + b*np.sin(c*x+phase) + offset

# === Lettura dati ===
cable_name = "short_2"
data_file = "data_cable_" + cable_name
save_as = "cable_att_fit_" + cable_name

# Assumi che il file ../data/misura_S21.txt contenga: freq, real, imag
data = np.loadtxt("../data/"+data_file + ".txt", delimiter="\t")

# Separa le colonne
f = data[:, 0]*1e9            # Frequenza in GHz 
real = data[:, 1]
imag = data[:, 2]

# Calcola modulo o potenza
# Se il tuo segnale è in dB, puoi fare:
# Se invece vuoi lavorare in potenza lineare:
amp = 10*np.log10(real**2+imag**2)
amp_filtered = savgol_filter(amp, 100, 4)  # Filtro Savitzky-Golay
p0 = [-0.5, 
      2, 
      5, 
      0, 
      0, 
      #-0.05
      ] # a * np.exp(-b * x) + c*np.sin(d*x+phase) + offset
# === Fit ===
popt, pcov = curve_fit(attenuation_fit, f, amp_filtered, p0=p0)

# === Plot ===
f_fit = np.linspace(f.min(), f.max(), 2000)
y_fit = attenuation_fit(f_fit, *popt)

fig, ax = plt.subplots()

#----Signal plot-----
ax.plot(f, amp, '-', markersize = 3,label="Data")
ax.plot(f, amp_filtered, '-', label="Filtered Data")
ax.plot(f_fit, y_fit, '-', label="Fit Attenuation")
#ax.plot(f_fit, y_fit, '-', label="Fit Resonance")
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("Amplitude (dBm)")
#ax_mag.grid(True, alpha=0.3)
ax.set_title("Magnitude")
ax.legend()

save_as += ".pdf"
fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data/{save_as}")

plt.show()
