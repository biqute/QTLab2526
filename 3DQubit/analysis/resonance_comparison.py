from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

# === Lettura dati ===
n_misura = "0"
data_file = "2_10mK_MKID" + n_misura

data = np.loadtxt("../cryo2/" + data_file + ".txt", delimiter="\t")

f_1 = data[:, 0]
real_1 = data[:, 1]
imag_1 = data[:, 2]
module_1 = np.sqrt(real_1**2 + imag_1**2)

# === Plot ===
fig, ax = plt.subplots()

# --- Base resonance ---
#ax.plot(f_1/1e9, module_1, '-', label=r"$10\,mK$")

# --- Temperature-dependent resonances ---
Temps = ["25mK", "300mK", "400mK", "500mK", "600mK", "700mK", "800mK", "900mK", "1000mK", "1100mK", "1200mK", "1300mK"]

for t in Temps:
    data_t = np.loadtxt(f"../T_dep/MKID_resonance_{t}.txt", delimiter="\t")
    f_t      = data_t[:, 0]  # Converti in GHz
    real_t   = data_t[:, 1]
    imag_t   = data_t[:, 2]
    module_t = np.sqrt(real_t**2 + imag_t**2)
    ax.plot(f_t/1e9, module_t, '-', label=rf"${t}$", color = plt.cm.Reds(float(Temps.index(t)) / len(Temps)))

ax.set_xlabel(r"$f\ \,[\mathrm{GHz}]$")
ax.set_ylabel(r"$|S_{21}|$")
ax.set_title("Resonance analysis")
ax.legend(loc='best')
ax.grid(True, alpha=0.3)



save_as = "moving_resonances_plot"
fig.savefig(f"../T_dep/{save_as}.png", bbox_inches="tight")

save_as += ".pdf"
fig.savefig(f"../T_dep/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../T_dep/{save_as}")

plt.tight_layout()


plt.show()