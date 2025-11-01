import os
import pandas as pd
import matplotlib.pyplot as plt

# ============================
# Impostazioni grafiche
# ============================
plt.rcParams.update({
    "text.usetex": False,             # NON usare LaTeX esterno (evita errore)
    "mathtext.fontset": "stix",       # Stile dei simboli matematici
    "font.family": "DejaVu Sans",     # Font leggibile e compatibile
    "font.size": 14,                  # Dimensione testo generale
    "axes.labelsize": 16,             # Etichette assi
    "axes.titlesize": 18,             # Titolo grafico
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "axes.linewidth": 1.2,
    "lines.linewidth": 2,
    "lines.markersize": 7,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
    "figure.figsize": (7, 5)
})

# ============================
# Percorso file CSV
# ============================
script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, r"C:\Users\kid\QTLab2526\QTLab2526\SinglePhoton\Data\S11_data.csv")

# ============================
# Lettura dati
# ============================
df = pd.read_csv(file_path)

frequenze = df["Frequenza (Hz)"] / 1e9  # in GHz
re_s11 = df["Re(S11)"]
im_s11 = df["Im(S11)"]

# ============================
# Creazione grafico
# ============================
fig, ax = plt.subplots()

# Parte reale (blu)
#ax.plot(re_s21, re_s21, marker='o', color='royalblue', label=r'$\mathrm{Re}(S_{21})$')

# Parte immaginaria (arancione)
ax.plot(re_s11, im_s11, marker='s', color='darkorange', label=r'$\mathrm{Im}(S_{11})$')

# Etichette e titolo
ax.set_xlabel(r"Re($S_{11}$)")
ax.set_ylabel(r"Im($S_{11}$)")
ax.set_title(r"Componente reale e immaginaria di $S_{11}$")

# Griglia e legenda
ax.grid(True)
ax.legend(frameon=True, loc="best", fontsize=12)

# Migliora layout
plt.tight_layout()

# Mostra grafico
plt.show()
