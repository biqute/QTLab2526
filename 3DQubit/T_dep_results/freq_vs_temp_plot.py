import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. Caricamento dei dati
# ==========================================
# Dati: Frequenza
data_freq = np.loadtxt("Resonance_vs_Temperature.txt", delimiter="\t")
temperature_mK_freq = data_freq[:, 0]  
frequency_Hz = data_freq[:, 1]

# Dati: 1/Q 
data_revQ = np.loadtxt("revQ_vs_Temperature.txt", delimiter="\t")
temperature_mK_revQ = data_revQ[:, 0]  
revQ = data_revQ[:, 1]

# Errore sulle temperature (10 mK)
T_err = 10

# ==========================================
# 2. Creazione dei grafici (Affiancati)
# ==========================================
# Modifica qui: 1 riga, 2 colonne. Ho anche aumentato la larghezza (figsize=(14, 5))
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# --- GRAFICO 1: Frequenza vs Temperatura (A Sinistra) ---
ax1.errorbar(temperature_mK_freq, frequency_Hz/1e9, xerr=T_err, fmt='o', color='blue', 
             ecolor='red', capsize=3, capthick=1, markersize=5, 
             label='Frequency')

ax1.set_xlabel("Temperature (mK)")
ax1.set_ylabel("Resonance Frequency (GHz)")
ax1.set_title("Resonance Frequency vs Temperature")
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend()

# --- GRAFICO 2: 1/Q vs Temperatura (A Destra) ---
ax2.errorbar(temperature_mK_revQ, revQ, xerr=T_err, fmt='o', color='green', 
             ecolor='orange', capsize=3, capthick=1, markersize=5, 
             label='1/Q')

ax2.set_xlabel("Temperature (mK)")
ax2.set_ylabel("1/Q")
ax2.set_title("1/Q vs Temperature")
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend()

# ==========================================
# 3. Salvataggio e visualizzazione
# ==========================================
# Allinea e distanzia automaticamente i grafici per evitare sovrapposizioni
plt.tight_layout()

# Salvataggio
plt.savefig("freq_and_revQ_vs_temp.png", dpi=300) 
plt.show()