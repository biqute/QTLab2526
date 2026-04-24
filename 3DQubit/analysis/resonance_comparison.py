from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl  # Aggiunto per gestire la colorbar

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

# === Plot ===
fig, ax = plt.subplots()

# --- Temperature-dependent resonances ---
Temps = [
    "10mK", 
    "200mK_b", 
    "300mK_b", 
    "400mK_b",  
    "500mK_b", "550mK_b", "600mK_b", "650mK_b", "675mK_b", 
    "700mK", "725mK", "750mK", "775mK",
    "800mK", "825mK", "850mK", "875mK_b","900mK","925mK_b",
    "950mK", "975mK", "1000mK", 
]

# 1. Estraiamo i valori numerici (float) pulendo le stringhe
T_nums = [float(t.replace("mK_b", "").replace("mK", "")) for t in Temps]

# 2. Creiamo la normalizzazione e scegliamo la colormap
cmap_name = 'jet'  # Prova anche 'viridis', 'inferno' o 'coolwarm'
cmap = plt.get_cmap(cmap_name)
norm = mpl.colors.Normalize(vmin=min(T_nums), vmax=max(T_nums))

for i, t in enumerate(Temps):
    data_t = np.loadtxt(f"../T_dep/2_MKID_resonance_{t}.txt", delimiter="\t")
    f_t      = data_t[:, 0]  # Converti in GHz
    real_t   = data_t[:, 1]
    imag_t   = data_t[:, 2]
    module_t = 20*np.log10(np.sqrt(real_t**2 + imag_t**2))
    
    # 3. Calcoliamo il colore esatto associato al valore di temperatura
    color = cmap(norm(T_nums[i]))
    # 4. Logica di evidenziazione per "10mK" (prima traccia)
    if i == 0:
        lw_style = 1.5      # Linea molto più spessa
        alpha_style = 1.0   # Nessuna trasparenza
        zorder_style = 10   # Sopra tutte le altre
    else:
        lw_style = 1.0      # Spessore standard
        alpha_style = 0.7   # Leggera trasparenza per chiarezza visiva
        zorder_style = 1

    ax.plot(f_t/1e9, module_t, '-', 
            color=color, 
            linewidth=lw_style, 
            alpha=alpha_style, 
            zorder=zorder_style)
    # Non passiamo più 'label' perché useremo la colorbar
    ax.plot(f_t/1e9, module_t, '-', color=color)

ax.set_xlabel("Frequency [GHz]", fontsize = 14)
ax.set_ylabel(r"Transmission [dB]", fontsize=14)
ax.grid(True, alpha=0.3)
ax.set_xlim(7.445, 7.51)

# 4. Creiamo e aggiungiamo la colorbar sulla destra
sm = mpl.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])  # Necessario per i ScalarMappable senza un plot 2D associato
cbar = fig.colorbar(sm, ax=ax)
cbar.set_label(r'Temperature [mK]', fontsize=14)

save_as = "moving_resonances_plot_final"
fig.savefig(f"../T_dep_results/{save_as}.png", bbox_inches="tight")

save_as += ".pdf"
fig.savefig(f"../T_dep_results/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../T_dep_results/{save_as}")

plt.tight_layout()
plt.show()