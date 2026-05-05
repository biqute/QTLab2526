from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

# 1. Caricamento e pulizia dei dati
# invalid_raise=False ignora le righe testuali (o di errore) a fine file
data = np.genfromtxt('sonnet_data/Lk_0.csv', delimiter=',', invalid_raise=False)
data = data[~np.isnan(data[:, 0])] # Rimuove eventuali righe vuote lette come NaN

frequencies = data[:, 0]
real_S21 = data[:, 5]
imag_S21 = data[:, 6]

# Calcolo del modulo in dB
module_S21 = 20 * np.log10(np.sqrt(real_S21**2 + imag_S21**2))

# 2. Suddivisione delle risonanze
# Troviamo gli indici in cui la frequenza "torna indietro" (fine di uno sweep e inizio del successivo)
split_indices = np.where(np.diff(frequencies) < 0)[0] + 1

freq_sweeps = np.split(frequencies, split_indices)
module_sweeps = np.split(module_S21, split_indices)

# 3. Valori di L_k (DA MODIFICARE CON I TUOI VALORI REALI)
# Creiamo un array fittizio, ad esempio 15 valori equidistanti tra 10 e 150 pH/sq
# Sostituiscilo con la tua lista di valori reali: es. Lk_nums = [10, 20, 30, ...]
Lk_nums = np.linspace(0, 15, len(freq_sweeps)) 

# === Plot ===
fig, ax = plt.subplots(figsize=(8, 6))

# Creiamo la normalizzazione e scegliamo la colormap (es. jet)
cmap_name = 'jet'  
cmap = plt.get_cmap(cmap_name)
norm = mpl.colors.Normalize(vmin=min(Lk_nums), vmax=max(Lk_nums))

for i, (f_swp, mod_swp) in enumerate(zip(freq_sweeps, module_sweeps)):
    
    # Calcoliamo il colore esatto associato al valore di L_k
    color = cmap(norm(Lk_nums[i]))

    lw_style = 2     # Spessore standard
    alpha_style = 0.7   # Leggera trasparenza per chiarezza visiva
    zorder_style = 1

    ax.plot(f_swp, mod_swp, '-', 
            color=color, 
            linewidth=lw_style, 
            alpha=alpha_style, 
            zorder=zorder_style)

ax.set_xlabel(r"Frequency (GHz)", fontsize=14)
ax.set_ylabel(r"Transmission (dB)", fontsize=14)
ax.grid(True, alpha=0.3)
# ax.set_xlim(...) # Decommenta se vuoi restringere la visualizzazione

# 4. Creiamo e aggiungiamo la colorbar sulla destra
sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # Necessario per i ScalarMappable senza un plot 2D associato
cbar = fig.colorbar(sm, ax=ax)
cbar.set_label(r'Kinetic Inductance $L_k$ (pH/sq)', fontsize=14) # Cambia le unità se necessario

# Salvataggio
save_as = "Lk_sweep_plot"
fig.savefig(f"{save_as}.png", bbox_inches="tight", dpi=300)

save_as += ".pdf"
fig.savefig(f"{save_as}", bbox_inches="tight")
print(f"Grafico salvato come {save_as}")

plt.tight_layout()
plt.show()