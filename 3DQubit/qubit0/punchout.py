import numpy as np
import os
import matplotlib.pyplot as plt
import sys
sys.path.append("/")

potenze = np.arange(-45, 6, 3)
num_potenze = len(potenze)

num_punti_freq = 8001 

# all 0 grid
signal_grid = np.zeros((num_potenze, num_punti_freq))
phase_grid  = np.zeros((num_potenze, num_punti_freq))
freq_grid   = np.zeros(num_punti_freq)

for i, p in enumerate(potenze):
    data_file = f"power_{p}"
    file_path = f"Data/{data_file}.txt"
    
    if not os.path.exists(file_path):
        print(f"Salto {file_path}: non trovato. Quella riga resterà a zero.")
        continue
        
    data = np.loadtxt(file_path, delimiter="\t")
    
    #salvataggio asse frequenze
    if i == 0:
        freq_grid[:] = data[:, 0] / 1e9
        
    real_S21 = data[:, 1]
    imag_S21 = data[:, 2]
    frequencies = data[:, 0]/1e9
    print(f"File {data_file}: {len(frequencies)} punti")

    S21_complex = real_S21 + 1j * imag_S21
    
    #costruisco griglia
    signal_grid[i, :] = 20 * np.log10(np.abs(S21_complex))
    phase_grid[i, :]  = np.unwrap(np.angle(S21_complex))


#Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

mappa_ampiezza = ax1.pcolormesh(freq_grid, potenze, signal_grid, cmap='magma', shading='auto')

ax1.set_xlabel('Frequency(GHz)', fontsize=12)
ax1.set_ylabel('Power (dBm)', fontsize=12)
cbar1 = fig.colorbar(mappa_ampiezza, ax=ax1)
cbar1.set_label('$|S_{21}|$ (dB)', fontsize=12)


mappa_fase = ax2.pcolormesh(freq_grid, potenze, phase_grid, cmap='magma', shading='auto')

ax2.set_xlabel('Frequency (GHz)', fontsize=12)
ax2.set_ylabel('Power (dBm)', fontsize=12)
cbar2 = fig.colorbar(mappa_fase, ax=ax2)
cbar2.set_label('Arg($S_{21}$) (Rad)', fontsize=12)

fig.suptitle('Qubit Punchout', fontsize=18, fontweight='bold')

fig.savefig(f"Plots/punchout.pdf", bbox_inches="tight")


plt.tight_layout()
plt.show()