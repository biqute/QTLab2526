import numpy as np
import os

# Parametri
mu_r = 1
epsilon_r = 1.0006
p_prime = 1.841
p = 2.405
a = 26e-3
d = 68.1e-3
c = 3e8

# Errori
err_c = 1e-3     # m/s
err_d = 1e-3     # m

# ---- LETTURA DEL FILE ----
nome_file = input("Inserisci il percorso del file CSV (ad esempio, 'data/dati_s21.csv'): ")

if not os.path.isfile(nome_file):
    print(f"Errore: il file {nome_file} non esiste.")
    exit()

# Carica il file (salta la prima riga se è intestazione)
data = np.loadtxt(nome_file, delimiter=",", skiprows=1)

# ---- CALCOLO PEAK ----
# colonna 0 = frequenza
# colonna 3 = ampiezza

idx_max = np.argmax(data[:, 3])
freq_max = data[idx_max, 0]
amp_max  = data[idx_max, 3]

print("\n--- RISULTATI MISURE ---")
print("Ampiezza massima       :", amp_max)
print("Frequenza corrispondente:", freq_max/1e9)


# ---- CALCOLO MODELLI TE e TM ----

TE_111 = (c/(2*np.pi)) * np.sqrt((p_prime/a)**2 + (np.pi/d)**2)
TM_010 = (c/(2*np.pi)) * (p/a)

A = (p_prime/a)**2
B = (np.pi/d)**2
K = c/(2*np.pi)

dfdc_TE = (1/(2*np.pi)) * np.sqrt(A + B)
dfdd_TE = -(K * np.pi**2) / (d**3 * np.sqrt(A + B))

dfdc_TM = (1/(2*np.pi)) * (p/a)

# Propagazione degli errori
err_TE = np.sqrt((dfdc_TE * err_c)**2 + (dfdd_TE * err_d)**2)
err_TM = dfdc_TM * err_c

print("\n--- FREQUENZE TEORICHE ---")
print(f"TE_111 = {TE_111/1e9:.6f} ± {err_TE/1e9:.6f} GHz")
print(f"TM_010 = {TM_010/1e9:.6f} ± {err_TM/1e9:.6f} GHz")

print("\nPeak sperimentale =", freq_max/1e9, "GHz")
