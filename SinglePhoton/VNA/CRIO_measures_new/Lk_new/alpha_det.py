import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# ==========================================
# 1. CARICAMENTO DATI E FIT BASE
# ==========================================
df = pd.read_csv('Frequenze_Minimi.csv', sep=',')
df.columns = df.columns.str.strip()

Lk_data = df['Lk'].values
f0_data = df['Frequenza_Minimo_GHz'].values

# Inserimento manuale Lk=0.0
Lk_data = np.insert(Lk_data, 0, 0.0)
f0_data = np.insert(f0_data, 0, 14.53)

# Errore di fit
sigma_f0 = np.full(len(f0_data), 0.02)

def res_freq(Lk, Lgeo, C):
    return 1.0 / (2 * np.pi * np.sqrt((Lgeo + Lk) * C))

# Esecuzione del fit per recuperare i parametri e la matrice di covarianza (pcov)
popt, pcov = curve_fit(res_freq, Lk_data, f0_data, p0=[5.0, 0.0001], sigma=sigma_f0, absolute_sigma=True, bounds=([0, 0], [np.inf, np.inf]))
Lgeo_opt, C_opt = popt

# ==========================================
# 2. CALCOLO DELLA KINETIC INDUCTANCE FRACTION (ALPHA) E DEL SUO ERRORE
# ==========================================
f_target = 7.4922873822
omega = 2 * np.pi * f_target

# Ricalcoliamo Lk per la frequenza target (dovrebbe dare ~13.92)
Lk_estrapolato = (1.0 / (omega**2 * C_opt)) - Lgeo_opt

# Calcolo del parametro alpha
alpha = Lk_estrapolato / (Lgeo_opt + Lk_estrapolato)

# PROPAGAZIONE DELL'ERRORE (Tramite Matrice Jacobiana)
# alpha in funzione dei parametri di fit diventa: alpha = 1 - (omega^2 * Lgeo * C)
# 1. Derivata parziale di alpha rispetto a Lgeo
d_alpha_dLgeo = -(omega**2) * C_opt
# 2. Derivata parziale di alpha rispetto a C
d_alpha_dC = -(omega**2) * Lgeo_opt

# Costruiamo il vettore Jacobiano
J = np.array([d_alpha_dLgeo, d_alpha_dC])

# Calcolo della varianza tramite matrice di covarianza (pcov): var = J * pcov * J^T
var_alpha = np.dot(J, np.dot(pcov, J))
err_alpha = np.sqrt(var_alpha)

# ==========================================
# 3. STAMPA DEI RISULTATI
# ==========================================
print("\n" + "="*40)
print("  RISULTATI KINETIC INDUCTANCE FRACTION")
print("="*40)
print(f"Frequenza Target: f  = {f_target:.4f} GHz")
print(f"Induttanza Geom : Lg = {Lgeo_opt:.4f} (dal fit)")
print(f"Induttanza Cin  : Lk = {Lk_estrapolato:.4f} (estrapolata)\n")

print(f"Valore di Alpha : a  = {alpha:.5f} ± {err_alpha:.5f}")
print("="*40 + "\n")