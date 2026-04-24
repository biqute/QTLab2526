import numpy as np
import matplotlib.pyplot as plt

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

# === Lettura dati ===
n_misura = "amp_range"
data_file = "data_10mK_" + n_misura
save_as = "only_plot_" + n_misura

data = np.loadtxt("10mK_resonances/data_10mK/" + data_file + ".txt", delimiter="\t")

# Separa le colonne
f = data[:, 0]              # Frequenza
real = data[:, 1]
imag = data[:, 2]

# Calcola modulo
y = 20*np.log10(np.sqrt(real**2 + imag**2))  # in dB, se vuoi in lineare rimuovi 20*np.log10
min_idx = np.argmin(y)
min_f = f[min_idx]
# === Plot ===
fig, ax = plt.subplots()

ax.plot(f/1e9, y, color = 'blue', label = "S21 Data")  # Frequenza in GHz
ax.set_xlabel("Frequency (GHz)", fontsize = 14)   # cambia in GHz se necessario
ax.set_ylabel("Transmission (dB)", fontsize = 14)  
#ax.set_title("Magnitude")
#ax.set_xlim(5, 9.1)
#ax.legend(loc='upper right')
ax.grid(True)

# Tick dei valori sugli assi
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
# === Salvataggio ===
save_as += ".pdf"
fig.savefig(f"10mK_resonances/plots_Giachero/{save_as}", bbox_inches="tight")

print(f"Grafico salvato in 10mK_resonances/plots_Giachero/{save_as}")

plt.show()