import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq

########## IMPOSTAZIONI GRAFICHE (Aesthetic Improvements) #####
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

data = np.loadtxt("../signalGen/drag_env_data.txt")


t = data[:, 0]  # Tempo square
y = data[:, 1]  # Ampiezza square (mV)

# Manteniamo solo i campioni con t > 200
mask = t > 300
if not np.any(mask):
    raise ValueError("Nessun campione con t > 200 trovato nel dataset")

t = t[mask]
y = y[mask]

# 2. Parametri di campionamento
dt_sec = (t[1] - t[0]) * 1e-6
fs = 1 / dt_sec              
n = len(t)             

# -----------------------------------------------------------
# 3. Calcolo della FFT con ZERO-PADDING
# -----------------------------------------------------------

# Scegliamo un fattore di zero padding. 
# 10 significa che aggiungiamo zeri fino a rendere l'array 10 volte più lungo.
# Più è alto, più la curva sarà smooth.
padding_factor = 10 

n_pad = n * padding_factor

# Generiamo i vettori di frequenza usando la NUOVA lunghezza paddata
# (Il dt rimane lo stesso!)
freq = fftfreq(n_pad, d=dt_sec) 

# Calcoliamo la FFT dicendo a numpy di allungare l'array fino a n_pad
# Numpy aggiungerà automaticamente gli zeri necessari in coda.
X = fft(y, n=n_pad)

# Prendiamo la metà positiva dello spettro
half_n = n_pad // 2

# CRITICO: Dividiamo SEMPRE per n (la lunghezza originale), NON per n_pad!
amp = (2.0 / n) * np.abs(X[:half_n])
freq_plot = freq[:half_n]
# (A questo punto puoi salvare i dati e fare i plot esattamente come prima)

# Salvataggio dati FFT in Hz
data_to_save = np.column_stack((freq_plot, amp))
np.savetxt("../signalGen/fft_FAST.txt", data_to_save, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')


# ==========================================
# 4. VISUALIZZAZIONE E SALVATAGGIO GRAFICI
# ==========================================

# ---------------- GRAFICO 1: TEMPO ----------------
fig1, ax1 = plt.subplots(figsize=(8, 6))

ax1.plot(t, y, label='Pulse', color='navy', alpha=0.85, lw=1.5)

ax1.set_xlabel(r"Time ($\mu s$)")
ax1.set_ylabel(r"Amplitude (mV)")
ax1.grid(True, which='major', linestyle='--', alpha=0.6)
ax1.legend(loc="upper right")

fig1.tight_layout()
fig1.savefig("../signalGen/FAST_time_domain.pdf")


# ---------------- GRAFICO 2: FREQUENZA ----------------
fig2, ax2 = plt.subplots(figsize=(8, 6))

# Divido per 1e3 per mostrare la frequenza in kHz (esteticamente più pulito)
freq_kHz = freq_plot / 1e3 

ax2.plot(freq_kHz-0.5, amp, label='Spectrum', color='navy', alpha=0.85, lw=1.5)

ax2.set_xlabel(r"Frequency (kHz)")
ax2.set_ylabel(r"Amplitude (mV)")
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.axvline(x=15, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Target (15 kHz)')
ax2.legend(loc="upper right")

# Calcolo del limite X direttamente in MHz
#limit_x_MHz = (min(fs_s, fs_g) / 20) / 1e3
ax2.set_xlim(0, 50)
#ax2.set_yscale('log')
fig2.tight_layout()
fig2.savefig("../signalGen/FAST_fft_freqDomain.pdf")

plt.show()