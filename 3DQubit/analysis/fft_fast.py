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
data_square = np.loadtxt("../signalGen/square_env_data.txt")
data_gaus = np.loadtxt("../signalGen/gaus_env_data.txt")
data_drag = np.loadtxt("../signalGen/drag_env_data.txt") # NUOVO DRAG

t_s = data_square[:, 0]  # Tempo square
y_s = data_square[:, 1]  # Ampiezza square (mV)

t_g = data_gaus[:, 0]    # Tempo gaussiano
y_g = data_gaus[:, 1]    # Ampiezza gaussiana (mV)

t_d = data_drag[:, 0]    # Tempo DRAG (NUOVO)
y_d = data_drag[:, 1]    # Ampiezza DRAG (mV) (NUOVO)

# Applicazione maschera su t_d: manteniamo solo t_d > 200
mask_d = t_d > -200
if not np.any(mask_d):
    raise ValueError("Nessun campione DRAG con t_d > -200 trovato nel dataset")

t_d = t_d[mask_d]
y_d = y_d[mask_d]

# ===========================================================
# 2. Parametri di campionamento
# ===========================================================
dt_s_sec = (t_s[1] - t_s[0]) * 1e-6
fs_s = 1 / dt_s_sec              
n_s = len(t_s)             

dt_g_sec = (t_g[1] - t_g[0]) * 1e-6
fs_g = 1 / dt_g_sec              
n_g = len(t_g)             

dt_d_sec = (t_d[1] - t_d[0]) * 1e-6  # NUOVO
fs_d = 1 / dt_d_sec                  # NUOVO
n_d = len(t_d)                       # NUOVO

# ===========================================================
# 3. Calcolo della FFT con ZERO-PADDING
# ===========================================================

# Scegliamo un fattore di zero padding. 
# 10 significa che aggiungiamo zeri fino a rendere l'array 10 volte più lungo.
padding_factor = 10 

n_s_pad = n_s * padding_factor
n_g_pad = n_g * padding_factor
n_d_pad = n_d * padding_factor       # NUOVO

# Generiamo i vettori di frequenza usando la NUOVA lunghezza paddata
freq_s = fftfreq(n_s_pad, d=dt_s_sec) 
freq_g = fftfreq(n_g_pad, d=dt_g_sec) 
freq_d = fftfreq(n_d_pad, d=dt_d_sec) # NUOVO

# Calcoliamo la FFT
X_square = fft(y_s, n=n_s_pad)
X_gaus = fft(y_g, n=n_g_pad)
X_drag = fft(y_d, n=n_d_pad)          # NUOVO

# Prendiamo la metà positiva dello spettro e normalizziamo divendo per la lunghezza originale (n)
half_n_s = n_s_pad // 2
freq_plot_s = freq_s[:half_n_s]
amp_square = (2.0 / n_s) * np.abs(X_square[:half_n_s])

half_n_g = n_g_pad // 2                      
freq_plot_g = freq_g[:half_n_g]          
amp_gaus = (2.0 / n_g) * np.abs(X_gaus[:half_n_g])

half_n_d = n_d_pad // 2                      # NUOVO
freq_plot_d = freq_d[:half_n_d]              # NUOVO
amp_drag = (2.0 / n_d) * np.abs(X_drag[:half_n_d]) # NUOVO

# Salvataggio dati FFT in Hz
data_to_save_s = np.column_stack((freq_plot_s, amp_square))
np.savetxt("../signalGen/fft_square.txt", data_to_save_s, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

data_to_save_g = np.column_stack((freq_plot_g, amp_gaus))
np.savetxt("../signalGen/fft_gauss.txt", data_to_save_g, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

data_to_save_d = np.column_stack((freq_plot_d, amp_drag))    # NUOVO
np.savetxt("../signalGen/fft_drag.txt", data_to_save_d, fmt='%.6f', header="Freq(Hz)\tAmp(mV)", delimiter='\t')

# ===========================================================
# 4. VISUALIZZAZIONE E SALVATAGGIO GRAFICI
# ===========================================================

# ---------------- GRAFICO 1: TEMPO ----------------
fig1, ax1 = plt.subplots(figsize=(8, 6))

ax1.plot(t_s, y_s, label='Square Pulse', color='navy', alpha=0.85, lw=1.5)
ax1.plot(t_g, y_g, label='Gaussian Pulse', color='darkorange', alpha=0.9, lw=2.5)
ax1.plot(t_d, y_d, label='DRAG Pulse', color='forestgreen', alpha=0.9, lw=2.0) # NUOVO

ax1.set_xlabel(r"Time ($\mu s$)")
#ax1.set_ylabel(r"Amplitude")
ax1.grid(True, which='major', linestyle='--', alpha=0.6)
ax1.legend(loc="upper right")
ax1.set_yscale('log')  # Usa scala lineare per l'asse y
fig1.tight_layout()
fig1.savefig("../signalGen/time_domain_PICO.pdf")

# ---------------- GRAFICO 2: FREQUENZA ----------------
fig2, ax2 = plt.subplots(figsize=(8, 6))

# Divido per 1e3 per mostrare la frequenza in kHz (rinominato da MHz a kHz per correttezza)
freq_kHz_s = freq_plot_s / 1e3 
freq_kHz_g = freq_plot_g / 1e3
freq_kHz_d = freq_plot_d / 1e3 # NUOVO

ax2.plot(freq_kHz_s, amp_square, label='Square Spectrum', color='navy', alpha=0.85, lw=1.5)
ax2.plot(freq_kHz_g, amp_gaus, label='Gauss Spectrum', color='darkorange', alpha=0.9, lw=2.5)
ax2.plot(freq_kHz_d-0.55, amp_drag, label='DRAG Spectrum', color='forestgreen', alpha=0.9, lw=2.0) # NUOVO

ax2.set_xlabel(r"Frequency (kHz)")
ax2.set_ylabel(r"Amplitude")
ax2.grid(True, which='both', linestyle='--', alpha=0.6)
ax2.axvline(x=15, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Target (15 kHz)')
ax2.legend(loc="upper right")

# Calcolo del limite X direttamente in kHz prendendo la frequenza di campionamento minima
limit_x_kHz = (min(fs_s, fs_g, fs_d) / 20) / 1e3
ax2.set_xlim(0, limit_x_kHz)

fig2.tight_layout()
fig2.savefig("../signalGen/fft_domain_PICO.pdf")

plt.show()