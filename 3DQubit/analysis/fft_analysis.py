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

# 1. Caricamento dati 
data_square = np.loadtxt("../data/square_env_data_new.txt")
data_gaus = np.loadtxt("../data/gaus_env_data_new.txt")

t_s = data_square[:, 0]  # Tempo square
y_s = data_square[:, 1]  # Ampiezza square (mV)

t_g = data_gaus[:,0]     # Tempo gaussiano
y_g = data_gaus[:, 1]    # Ampiezza gaussiana (mV)

# 2. Parametri di campionamento
dt_s_sec = (t_s[1] - t_s[0]) * 1e-6
fs_s = 1 / dt_s_sec              
n_s = len(t_s)             

dt_g_sec = (t_g[1] - t_g[0]) * 1e-6
fs_g = 1 / dt_g_sec              
n_g = len(t_g)             

# -----------------------------------------------------------
# 3. Calcolo della FFT con ZERO-PADDING
# -----------------------------------------------------------

# Scegliamo un fattore di zero padding. 
# 10 significa che aggiungiamo zeri fino a rendere l'array 10 volte più lungo.
# Più è alto, più la curva sarà smooth.
padding_factor = 10 

n_s_pad = n_s * padding_factor
n_g_pad = n_g * padding_factor

# Generiamo i vettori di frequenza usando la NUOVA lunghezza paddata
# (Il dt rimane lo stesso!)
freq_s = fftfreq(n_s_pad, d=dt_s_sec) 
freq_g = fftfreq(n_g_pad, d=dt_g_sec) 

# Calcoliamo la FFT dicendo a numpy di allungare l'array fino a n_pad
# Numpy aggiungerà automaticamente gli zeri necessari in coda.
X_square = fft(y_s, n=n_s_pad)
X_gaus = fft(y_g, n=n_g_pad)

# Prendiamo la metà positiva dello spettro
half_n_s = n_s_pad // 2
freq_plot_s = freq_s[:half_n_s]

# CRITICO: Dividiamo SEMPRE per n_s (la lunghezza originale), NON per n_s_pad!
amp_square = (2.0 / n_s) * np.abs(X_square[:half_n_s])

# Stessa cosa per la Gaussiana
half_n_g = n_g_pad // 2                      
freq_plot_g = freq_g[:half_n_g]          
amp_gaus = (2.0 / n_g) * np.abs(X_gaus[:half_n_g])

# (A questo punto puoi salvare i dati e fare i plot esattamente come prima)

# Salvataggio dati FFT in Hz
data_to_save_s = np.column_stack((freq_plot_s, amp_square))
np.savetxt("../data/fft_square.txt", data_to_save_s, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

data_to_save_g = np.column_stack((freq_plot_g, amp_gaus))
np.savetxt("../data/fft_gauss.txt", data_to_save_g, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

# ==========================================
# 4. VISUALIZZAZIONE E SALVATAGGIO GRAFICI
# ==========================================

# ---------------- GRAFICO 1: TEMPO ----------------
fig1, ax1 = plt.subplots(figsize=(8, 6))

ax1.plot(t_s, y_s, label='Square Pulse', color='navy', alpha=0.85, lw=1.5)
ax1.plot(t_g, y_g, label='Gaussian Pulse', color='darkorange', alpha=0.9, lw=2.5)

ax1.set_xlabel(r"Time ($\mu s$)")
ax1.set_ylabel(r"Amplitude (mV)")
ax1.grid(True, which='major', linestyle='--', alpha=0.6)
ax1.legend(loc="upper right")

fig1.tight_layout()
fig1.savefig("../data0_plots/time_domain_PICO.pdf")


# ---------------- GRAFICO 2: FREQUENZA ----------------
fig2, ax2 = plt.subplots(figsize=(8, 6))

# Divido per 1e6 per mostrare la frequenza in MHz (esteticamente più pulito)
freq_MHz_s = freq_plot_s / 1e3 - 3.5
freq_MHz_g = freq_plot_g / 1e3

ax2.plot(freq_MHz_s, amp_square, label='Square Spectrum', color='navy', alpha=0.85, lw=1.5)
ax2.plot(freq_MHz_g, amp_gaus, label='Gauss Spectrum', color='darkorange', alpha=0.9, lw=2.5)

ax2.set_xlabel(r"Frequency (kHz)")
ax2.set_ylabel(r"Amplitude (mV)")
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.axvline(x=15, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Target (15 kHz)')
ax2.legend(loc="upper right")

# Calcolo del limite X direttamente in MHz
limit_x_MHz = (min(fs_s, fs_g) / 20) / 1e3
ax2.set_xlim(0, limit_x_MHz)
#ax2.set_yscale('log')
fig2.tight_layout()
fig2.savefig("../data0_plots/fft_domain_PICO.pdf")

plt.show()