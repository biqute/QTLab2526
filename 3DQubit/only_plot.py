import numpy as np
import matplotlib.pyplot as plt

# Opzionale: impostazioni per il font
plt.rcParams.update({
    "text.usetex": False, # Metti True se hai LaTeX configurato nel tuo ambiente
    "font.family": "Helvetica"
})

# 1. Caricamento dati
# Usiamo invalid_raise=False per ignorare automaticamente le fastidiose 
# righe di testo in fondo al CSV di Sonnet
data = np.loadtxt('data/Delta_5Hz.txt', skiprows=2)

# Rimuoviamo eventuali righe vuote o header lette come NaN

time = data[:, 0]  # Frequenze
A_data = data[:, 1]     # Parte reale di S21
B_data = data[:, 2]     # Parte immaginaria di S21


plt.plot(time*1e3, A_data, label='Channel A', color='blue')
plt.plot(time*1e3, B_data, label='Channel B', color='darkorange')
plt.xlabel('Time (us)', fontsize=12)
plt.ylabel('Signal', fontsize=12)
plt.title('Acquisizione.txt data', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()