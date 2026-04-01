from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec 

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})


# === Lettura dati ===
data_file = "Q_vs_fr" 
save_as = "plot" + data_file

# Assumi che il file ../data/misura_S21.txt contenga: freq, real, imag
data = np.loadtxt("../data/"+data_file + ".txt", delimiter="\t")

# Separa le colonne
f_r = data[:, 0]              # Frequenza
Q_i = data[:, 1]

fig, ax = plt.subplots()

#----Signal plot-----
ax.plot(f_r, Q_i, '.', label="Dati (Q_i)")
ax.set_xlabel(r"$f_r[GHz]$")
ax.set_ylabel(r"$Q_i$")
#ax_mag.grid(True, alpha=0.3)
ax.set_title("Q_i vs f_r")
ax.semilogy()
save_as += ".pdf"
fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data0_plots/{save_as}")

plt.show()

