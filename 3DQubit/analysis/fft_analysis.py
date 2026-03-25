import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq

# 1. Caricamento dati 
data_square = np.loadtxt("../data/square_env_data_new.txt")
data_gaus = np.loadtxt("../data/gaus_env_data_new.txt")

t_s = data_square[:, 0]  # Tempo square
y_s = data_square[:, 1]  # Ampiezza square

t_g = data_gaus[:,0]     # Tempo gaussiano
y_g = data_gaus[:, 1]    # Ampiezza gaussiana

# 2. Parametri di campionamento per square
dt_s = t_s[1] - t_s[0]
dt_s_sec = dt_s * 1e-6       # CONVERSIONE IN SECONDI
fs_s = 1 / dt_s_sec              
n_s = len(t_s)             

# 2. Parametri di campionamento per gaussiano
dt_g = t_g[1] - t_g[0]     
dt_g_sec = dt_g * 1e-6       # CONVERSIONE IN SECONDI
fs_g = 1 / dt_g_sec              
n_g = len(t_g)             

# 3. Calcolo della FFT
freq_s = fftfreq(n_s, d=dt_s_sec) # Usa il dt in secondi!
freq_g = fftfreq(n_g, d=dt_g_sec) # Usa il dt in secondi!

X_square = fft(y_s)
X_gaus = fft(y_g)

# Consideriamo solo la metà positiva dello spettro per square
half_n_s = n_s // 2
freq_plot_s = freq_s[:half_n_s]
amp_square = np.abs(X_square[:half_n_s]) / n_s

# Consideriamo solo la metà positiva dello spettro per gaussiano
half_n_g = n_g // 2                      # AGGIUNTO
freq_plot_g = freq_g[:half_n_g]          # AGGIUNTO
amp_gaus = np.abs(X_gaus[:half_n_g]) / n_g

data_to_save = np.column_stack((freq_plot_s, amp_square))
np.savetxt("../data/fft_square.txt", data_to_save, fmt='%.6f', header="Freq(Hz) Amp(arb)", delimiter='\t')

data_to_save = np.column_stack((freq_plot_g, amp_gaus))
np.savetxt("../data/fft_gauss.txt", data_to_save, fmt='%.6f', header="Freq(Hz) Amp(arb)", delimiter='\t')


# 4. Visualizzazione
plt.figure(figsize=(14, 6))

# Subplot 1: Segnali nel tempo
plt.subplot(121)
plt.plot(t_s, y_s, label='Square', alpha=0.7)
plt.plot(t_g, y_g, label='Gauss', alpha=0.7, lw=2)
plt.title("Segnali nel dominio del Tempo")
plt.xlabel("Time (us)")
plt.legend()

# Subplot 2: Spettro di frequenza
plt.subplot(122)
# CORRETTO: Uso i rispettivi vettori di frequenza
plt.plot(freq_plot_s, amp_square, label='FFT Square')
plt.plot(freq_plot_g, amp_gaus, label='FFT Gauss', lw=2)
plt.title("Spettro di Frequenza")
plt.xlabel("Freq (Hz)")
plt.ylabel("Ampiezza")

# CORRETTO: Uso fs_s come riferimento per lo zoom (oppure puoi usare il minimo tra fs_s e fs_g)
limit_x = min(fs_s, fs_g) / 20
plt.xlim(0, limit_x) 
#plt.yscale('log')   
plt.legend()

plt.tight_layout()

nome_grafico = "fft_PICO.pdf"
plt.savefig(f"../data0_plots/{nome_grafico}")
plt.show()