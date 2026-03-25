import numpy as np
import matplotlib.pyplot as plt
from numpy.fft import fft, fftfreq

# 1. Caricamento dati 
data_square = np.loadtxt("data/fft_square.txt")
data_gaus = np.loadtxt("data/fft_gauss.txt")

t_s = data_square[:, 0]  # Tempo square
y_s = data_square[:, 1]  # Ampiezza square

t_g = data_gaus[:,0]     # Tempo gaussiano
y_g = data_gaus[:, 1]    # Ampiezza gaussiana


plt.plot(t_s, y_s, label='Square', alpha=0.7)
plt.plot(t_g, y_g, label='Gauss', alpha=0.7, lw=2)
plt.title("Fast Fourier Transform")
plt.xlabel("Frequency (us)")
plt.ylabel("Amplitude")
plt.xlim(0, 100e3)
plt.legend()
  
plt.legend()

plt.tight_layout()

nome_grafico = "fft_Final.pdf"
plt.savefig(f"data0_plots/{nome_grafico}")
plt.show()