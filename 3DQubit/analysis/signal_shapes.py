import numpy as np
import matplotlib.pyplot as plt

def square_pulse(t, width):
    """Genera un'onda quadra centrata in t=0 con larghezza specificata."""
    return np.where(np.abs(t) <= width / 2, 1.0, 0.0)

def gaussian_pulse(t, sigma):
    """Genera un impulso gaussiano centrato in t=0 con deviazione standard sigma."""
    return np.exp(-(t**2) / (2 * sigma**2))

def drag_pulse(t, sigma, beta):
    """Genera un impulso DRAG combinando una gaussiana e la sua derivata."""
    env_i = gaussian_pulse(t, sigma)
    env_q = -beta * (-t / sigma**2) * env_i  # Derivata scalata
    return env_i, env_q

# 1. Parametri Generali e di Simulazione
fc = 15e3
period = 1 / fc    # Periodo dell'onda sinusoidale (portante)
fs = 500e3        # Frequenza di campionamento
T_sim = 15*period   # Durata totale della simulazione
t = np.linspace(-T_sim/2, T_sim/2, int(T_sim * fs), endpoint=False)

# 2. Parametri degli Inviluppi
width_sq = 5 * period   # Larghezza dell'onda quadra: 200 us
sigma = width_sq/5  # Converti larghezza in dev std
beta_drag = 0.0005  # Coefficiente di ottimizzazione DRAG (scala la derivata)

# Generazione della Portante (Carrier)
carrier_I = np.cos(2 * np.pi * fc * t)
carrier_Q = np.sin(2 * np.pi * fc * t)

# --- A. Onda Quadra (Square Pulse) ---
# Inviluppo: 1 se |t| < width_sq / 2, altrimenti 0
env_square = square_pulse(t, width_sq)
pulse_square = env_square * carrier_I

# --- B. Impulso Gaussiano (Gaussian Pulse) ---
# Inviluppo: exp(-t^2 / (2 * sigma^2))
env_gauss = gaussian_pulse(t, sigma)
pulse_gauss = env_gauss * carrier_I

# --- C. Impulso DRAG ---
# Componente In-Phase (I) = Gaussiana
# Componente Quadrature (Q) = Derivata della Gaussiana (scalata da beta)
env_i, env_q = drag_pulse(t, sigma, beta_drag)
pulse_drag = env_i * carrier_I + env_q * carrier_Q

# 3. Analisi in Frequenza (FFT)
def compute_fft(signal, fs):
    # Calcola la FFT reale e le relative frequenze in kHz
    fft_vals = np.fft.rfft(signal)
    fft_freqs = np.fft.rfftfreq(len(signal), d=1/fs) / 1000 
    return fft_freqs, np.abs(fft_vals)

freqs_sq, mag_sq = compute_fft(pulse_square, fs)
freqs_gauss, mag_gauss = compute_fft(pulse_gauss, fs)
freqs_drag, mag_drag = compute_fft(pulse_drag, fs)

# 4. Visualizzazione Grafica (Riproduzione Figure 6 e 7)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Grafico nel Dominio del Tempo
# Per chiarezza visiva, riduciamo l'asse dei tempi attorno all'impulso
mask_t = (t >= -200e-6) & (t <= 200e-6)
ax1.plot(t[mask_t]*1e6, pulse_square[mask_t], label='Square Pulse', color='navy')
ax1.plot(t[mask_t]*1e6, pulse_gauss[mask_t], label='Gaussian Pulse', color='orange')
ax1.plot(t[mask_t]*1e6, pulse_drag[mask_t], label='DRAG Pulse', color='forestgreen')
ax1.set_title('Dominio del Tempo')
ax1.set_xlabel('Tempo ($\mu$s)')
ax1.set_ylabel('Ampiezza')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend()

# Grafico nello Spettro delle Frequenze
# Limitiamo la vista tra 0 e 40 kHz come in Fig 7
mask_f = (freqs_sq >= 0) & (freqs_sq <= 40)
ax2.plot(freqs_sq[mask_f], mag_sq[mask_f], label='Square Spectrum', color='navy')
ax2.plot(freqs_gauss[mask_f], mag_gauss[mask_f], label='Gauss Spectrum', color='orange')
ax2.plot(freqs_drag[mask_f], mag_drag[mask_f], label='DRAG Spectrum', color='forestgreen')
ax2.axvline(15, color='crimson', linestyle='--', label='Target (15 kHz)')
ax2.set_title('Spettro delle Frequenze (Trasformata di Fourier)')
ax2.set_xlabel('Frequenza (kHz)')
ax2.set_ylabel('Ampiezza')
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend()

plt.tight_layout()
plt.show()