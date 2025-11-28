import matplotlib.pyplot as plt
import numpy as np

# Carica dati dal file CSV con intestazione (salta la prima riga)
data = np.loadtxt("dati_diodo.csv", delimiter=",", skiprows=1)

# Estrai colonne
VDC = data[:, 0]   # colonna 0
VFD = data[:, 1]   # colonna 1
err = data[:, 2]   # colonna 2

# Crea plot con barre di errore
plt.figure(figsize=(10,6))
plt.errorbar(VDC, VFD, yerr=err, fmt='o', capsize=5, markersize=5, ecolor='red', color='blue', label='VFD ± devstd')
plt.xlabel('VDC (mV)')
plt.ylabel('VFD (mV)')
plt.title('VFD vs VDC con errori standard')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
