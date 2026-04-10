import numpy as np
import matplotlib.pyplot as plt

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

# === Lettura dati ===
n_misura = "500mK"
data_file = "2_MKID_resonance_" + n_misura
##save_as = "plot_" + data_file

data = np.loadtxt("T_dep/" + data_file + ".txt", delimiter="\t")

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

ax.plot(f, y, '.', label="Dati (|S21|)")
ax.set_xlabel(r"$f\,[\mathrm{Hz}]$")   # cambia in GHz se necessario
ax.set_ylabel(r"$|S_{21}|$")
ax.set_title("Magnitude")
#ax.set_xlim(min_f-5e6, min_f+5e6)
ax.legend(loc='upper right')
# === Salvataggio ===
#save_as += ".pdf"
#fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")

#print(f"Grafico salvato in ../data0_plots/{save_as}")

plt.show()