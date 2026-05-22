import numpy as np
import matplotlib.pyplot as plt

# Opzionale: impostazioni per il font
plt.rcParams.update({
    "text.usetex": False, # Metti True se hai LaTeX configurato nel tuo ambiente
    "font.family": "Helvetica"
})

filename = "IQ_mixer_data.txt"

data = np.loadtxt(f'data/{filename}', skiprows=2)

# Rimuoviamo eventuali righe vuote o header lette come NaN

time = data[:, 0]  # Frequenze
A_data = data[:, 1]     # canale A
B_data = data[:, 2]     # canale B

plt.plot(time*1e-6, A_data, label='Channel A', color='blue')
plt.plot(time*1e-6, B_data, label='Channel B', color='darkorange')
plt.xlabel('Time (ms)', fontsize=12)
plt.ylabel('Signal', fontsize=12)
plt.title(f'{filename} data', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()