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

## Fit function for attenuation by Prozark
#def attenuation_fit(x, a, b, c, d, phase, offset):
#    return offset + ( a*np.sqrt(x) + b*x ) *np.sin(c*x + phase) + d*x

### fit con esponenziale + sinusoide

def attenuation_fit(x, a, b, c, d, phase, offset):
    return a * np.exp(-b * x) + c*np.sin(d*x+phase) + offset
p0 = [1.5, # a
      0.551, # b
      0.02, # c
      -2, # d
      0, # phase
      -0.3 # offset
      ] 
'''
### fit lineare + sinusoide
def attenuation_fit(x, a, b, c, phase, offset):
   return a * x + b*np.sin(c*x+phase) + offset
p0 = [ -0.01,    # a
         0.033,   # b
         2e-4,    # c
         -2,      # phase
         -2       # offset
         ]
'''
'''
### fit esponenziale e basta
def attenuation_fit(x, a, b, offset):
    return a * np.exp(-b * x) + offset
p0 = [0.436, # a
      0.551, # b
      -0.299 # offset
      ]
'''

# === Lettura dati ===
cable_name = "long_2"
data_file = "data_cable_" + cable_name
save_as = "cable_att_fit_" + cable_name

# Assumi che il file contenga: freq, real, imag
data = np.loadtxt("../data/"+data_file + ".txt", delimiter="\t")

f = data[:, 0]*1e9            # Frequenza in GHz 
real = data[:, 1]
imag = data[:, 2]

amp = 10*np.log10(real**2+imag**2)
amp_filtered = savgol_filter(amp, 100, 4)  # Filtro Savitzky-Golay

# === Fit ===
popt, pcov = curve_fit(attenuation_fit, f, amp_filtered, p0=p0)
print("Fit parameters:")
for i, param in enumerate(popt):
    print(f"p[{i}] = {param:.3f} ± {np.sqrt(pcov[i, i]):.3f}")

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
ax.set_title("Attenuation plot for cable Long 2")
ax.legend()
not_title = True
if not_title:
    ax.set_title("")
    save_as += "_notitle"
save_as += ".pdf"
fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data/{save_as}") 
plt.show()
