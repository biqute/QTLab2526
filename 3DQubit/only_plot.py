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
data = np.genfromtxt('sonnet_sim/sonnet_data/Lk_0.csv', delimiter=',', invalid_raise=False)

# Rimuoviamo eventuali righe vuote o header lette come NaN
data = data[~np.isnan(data[:, 0])]

frequencies = data[:, 0]  # Frequenze
real_S21 = data[:, 5]     # Parte reale di S21
imag_S21 = data[:, 6]     # Parte immaginaria di S21

# Calcolo dell'ampiezza (in lineare, ma se preferisci i dB fai: 20 * np.log10(signal))
signal = np.abs(real_S21 + 1j * imag_S21)

# 2. Identificazione e separazione degli sweep
# np.diff calcola la differenza tra elementi consecutivi. 
# Quando la frequenza torna indietro (inizia un nuovo L_k), np.diff < 0.
split_indices = np.where(np.diff(frequencies) < 0)[0] + 1

# Suddividiamo gli array in base ai "salti" di frequenza trovati
freq_sweeps = np.split(frequencies, split_indices)
signal_sweeps = np.split(signal, split_indices)

# 3. Creazione del grafico
fig, ax = plt.subplots(figsize=(10, 6))

# Creiamo una palette di colori (colormap) per le 15 curve, da blu a giallo
colors = plt.cm.viridis(np.linspace(0, 1, len(freq_sweeps)))

for i, (f_swp, s_swp) in enumerate(zip(freq_sweeps, signal_sweeps)):
    # Plot di ogni singola risonanza
    ax.plot(f_swp, s_swp, '-', linewidth=2, color=colors[i], label=f'Sweep {i+1}')

ax.set_xlabel('Frequency (GHz)', fontsize=12)
ax.set_ylabel('$|S_{21}|$', fontsize=12)
ax.set_title('Risposta del Risonatore al variare dell\'Induttanza Cinetica $L_k$', fontsize=14)
ax.grid(True, alpha=0.3)

# Spostiamo la legenda fuori dal grafico per non coprire i dati
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Valori $L_k$")

plt.tight_layout()
plt.show()