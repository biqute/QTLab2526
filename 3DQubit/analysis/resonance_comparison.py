from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})


# === Plot ===
fig, ax = plt.subplots()

# --- Base resonance ---
#ax.plot(f_1/1e9, module_1, '-', label=r"$10\,mK$")

# --- Temperature-dependent resonances ---
Temps = [
        #"10mK", 
        # "200mK", 
         "300mK", 
         "400mK", 
         "500mK",
          "600mK", "700mK", "725mK", "750mK", "775mK","800mK", "825mK", "850mK", "875mK", "900mK",
          "925mK",
          "950mK",
          "975mK",
          "1000mK"
          ]

for t in Temps:
    data_t = np.loadtxt(f"../T_dep/2_MKID_resonance_{t}.txt", delimiter="\t")
    f_t      = data_t[:, 0]  # Converti in GHz
    real_t   = data_t[:, 1]
    imag_t   = data_t[:, 2]
    module_t = 20*np.log10(np.sqrt(real_t**2 + imag_t**2))
    #module_t = np.sqrt(real_t**2 + imag_t**2)
    ax.plot(f_t/1e9, module_t, '-', label=f"{t}"
            ,color = plt.cm.Reds(float(Temps.index(t)) / len(Temps))
            )

ax.set_xlabel(r"$f\ \,[\mathrm{GHz}]$")
ax.set_ylabel(r"$|S_{21}|$")
ax.set_title("Resonance analysis")
ax.legend(loc='best')
ax.grid(True, alpha=0.3)
ax.set_xlim(7.45, 7.525)


save_as = "2_moving_resonances_plot"
fig.savefig(f"../T_dep/{save_as}.png", bbox_inches="tight")

save_as += ".pdf"
fig.savefig(f"../T_dep/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../T_dep/{save_as}")

plt.tight_layout()


plt.show()