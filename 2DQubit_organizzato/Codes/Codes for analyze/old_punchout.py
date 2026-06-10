import numpy as np
import os
import matplotlib.pyplot as plt
import sys
sys.path.append("/")

potenze = np.arange(-48, 3, 3)
num_potenze = len(potenze)
num_punti_freq = 4000
percorso_cartella = r"C:\Users\kid\labQT\Lab2025"

signal_grid = np.zeros((num_potenze, num_punti_freq))
phase_grid  = np.zeros((num_potenze, num_punti_freq))
freq_grid   = np.zeros(num_punti_freq)

for i, p in enumerate(potenze):
    nome_file = f"data_power_{p}dBm.npz"
    data_file = os.path.join(percorso_cartella, nome_file)
    # 1. Carica il file .npz compresso
    data = np.load(data_file, allow_pickle=True)
    
    # 2. Accedi all'array strutturato
    struttura = data['0']
    
    # 3. Salvataggio asse frequenze (solo alla prima iterazione)
    if i == 0:
        freq_grid[:] = struttura['freq'] / 1e9
        
    print(f"File {data_file}: {len(struttura['freq'])} punti")

    signal_grid[i, :] = 20 * np.log10(struttura['signal'])
    
    
    phase_grid[i, :]  = np.unwrap(struttura['phase'])
    #phase_grid[i, :]  = struttura['phase']
    
# Calcoliamo la differenza di fase tra ogni gradino di potenza
# usando la prima colonna (indice 0), cioè una frequenza lontana dal Qubit
fase_background = phase_grid[:, 0]
salti_di_fase = np.diff(fase_background)

# Troviamo l'indice dove il salto è più drastico (l'attenuatore che scatta)
indice_salto = np.argmax(np.abs(salti_di_fase))

# 2. Calcoliamo di quanto è sfasato il blocco inferiore rispetto a quello superiore
fase_sotto_salto = phase_grid[indice_salto, 0]
fase_sopra_salto = phase_grid[indice_salto + 1, 0]
delta_fase = fase_sopra_salto - fase_sotto_salto

print(f"Salto di fase rilevato all'indice {indice_salto} (Potenza: {potenze[indice_salto]} dBm)")
print(f"Compensazione applicata: {delta_fase:.2f} radianti")

# 3. Applichiamo la compensazione a TUTTE le potenze inferiori o uguali al salto
phase_grid[:indice_salto + 1, :] += delta_fase

# 4. TRUCCO MAGICO: siccome abbiamo sommato una fase, potremmo essere usciti
# dal range [-pi, +pi]. Per rimettere tutto a posto senza distorcere nulla,
# convertiamo in numero complesso e ri-estraiamo l'angolo!
phase_grid = np.angle(np.exp(1j * phase_grid))

# =====================================================================
# PLOT DEI DATI
# =====================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot Ampiezza
mappa_ampiezza = ax1.pcolormesh(freq_grid, potenze, signal_grid, cmap='magma', shading='auto')
ax1.set_xlabel('Frequency (GHz)', fontsize=12)
ax1.set_ylabel('Power (dBm)', fontsize=12)
cbar1 = fig.colorbar(mappa_ampiezza, ax=ax1)
cbar1.set_label('$|S_{21}|$ (dB)', fontsize=12)

# Plot Fase
mappa_fase = ax2.pcolormesh(freq_grid, potenze, phase_grid, cmap='magma', shading='auto')
ax2.set_xlabel('Frequency (GHz)', fontsize=12)
ax2.set_ylabel('Power (dBm)', fontsize=12)
cbar2 = fig.colorbar(mappa_fase, ax=ax2)
cbar2.set_label('Arg($S_{21}$) (Rad)', fontsize=12)

fig.suptitle('Qubit Punchout', fontsize=18, fontweight='bold')
plt.tight_layout()
plt.show()


