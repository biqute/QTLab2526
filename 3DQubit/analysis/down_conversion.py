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

# ===========================================================
# 1. Caricamento dati 
# ===========================================================
filename = "IQ_mixer_data.txt"

data = np.loadtxt(f'../data/{filename}', skiprows=2)

# Rimuoviamo eventuali righe vuote o header lette come NaN

time = data[:, 0]  # Frequenze
A_data = data[:, 1]     # canale A
B_data = data[:, 2]     # canale B

# ===========================================================
# 2. Parametri di campionamento
# ===========================================================
dt_sec = (time[1] - time[0]) * 1e-9
fs = 1 / dt_sec              
n = len(time)             

# ===========================================================
# 3. Calcolo della FFT con ZERO-PADDING
# ===========================================================

# Scegliamo un fattore di zero padding. 
# 10 significa che aggiungiamo zeri fino a rendere l'array 10 volte più lungo.
padding_factor = 10 
n_pad = padding_factor * n

# Generiamo i vettori di frequenza usando la NUOVA lunghezza paddata
freq = fftfreq(n_pad, d=dt_sec) 

# Calcoliamo la FFT
X_a = fft(A_data, n=n_pad)
X_b = fft(B_data, n=n_pad)

# Prendiamo la metà positiva dello spettro e normalizziamo divendo per la lunghezza originale (n)
half_n = n_pad // 2
freq_plot = freq[:half_n]
amp_A = (2.0 / n) * np.abs(X_a[:half_n])
amp_B = (2.0 / n) * np.abs(X_b[:half_n])

# Salvataggio dati FFT in Hz
data_to_save_A = np.column_stack((freq_plot, amp_A))
np.savetxt("../IQ_mixer/fft_A.txt", data_to_save_A, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

data_to_save_B = np.column_stack((freq_plot, amp_B))
np.savetxt("../IQ_mixer/fft_B.txt", data_to_save_B, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

# ===========================================================
# 4. VISUALIZZAZIONE E SALVATAGGIO GRAFICI
# ===========================================================

# ---------------- GRAFICO 1: TEMPO ----------------
fig1, ax1 = plt.subplots(figsize=(8, 6))

ax1.plot(time, A_data, label='I', color='navy', alpha=0.85, lw=1.5)
ax1.plot(time, B_data, label='Q', color='darkorange', alpha=0.9, lw=2.5)

ax1.set_xlabel(r"Time ($\mu s$)")
#ax1.set_ylabel(r"Amplitude")
ax1.grid(True, which='major', linestyle='--', alpha=0.6)
ax1.legend(loc="upper right")

fig1.tight_layout()
fig1.savefig("../IQ_mixer/time_domanin_plot.pdf")

# ---------------- GRAFICO 2: FREQUENZA ----------------
fig2, ax2 = plt.subplots(figsize=(8, 6))

# Divido per 1e3 per mostrare la frequenza in kHz (rinominato da MHz a kHz per correttezza)
freq_kHz = freq_plot/1e3

ax2.plot(freq_kHz, amp_A, label='I Spectrum', color='navy', alpha=0.85, lw=1.5)
ax2.plot(freq_kHz, amp_B, label='Q Spectrum', color='darkorange', alpha=0.9, lw=2.5)

ax2.set_xlabel(r"Frequency (MHz)")
ax2.set_ylabel(r"Amplitude")
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.legend(loc="upper right", fontsize=14)
ax2.set_xlim(0, 400)  
fig2.tight_layout()
fig2.savefig("../IQ_mixer/fft_domain_plot.pdf")

plt.show()