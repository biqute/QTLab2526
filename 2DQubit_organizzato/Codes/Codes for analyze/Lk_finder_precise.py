from matplotlib import cm

import pandas as pd
import io
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


def estrai_dataset(file_path, lk_target):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    dataset_lines = []
    reading = False
    
    for line in lines:
        # Quando troviamo una riga che indica un nuovo set (es. Lk=15.0)
        if "Lk=" in line:
            if f"Lk={lk_target}" in line:
                reading = True
            else:
                if reading:
                    break  # Se abbiamo già letto il set, fermati al successivo "Lk="
            continue # Salta la riga specifica che contiene "Lk="
            
        if reading:
            dataset_lines.append(line)
            
    # Convertiamo la lista di righe in un comodo DataFrame Pandas
    df = pd.read_csv(io.StringIO("".join(dataset_lines)))
    return df

def lorentziana_inv(x, y0, A, x0, gamma):
    return y0 - A * (gamma**2 / ((x - x0)**2 + gamma**2))

file_csv = 'precision_Lk_scan_3.csv'
valori_lk = [f"{x:.1f}" for x in np.arange(10, 16.1, 0.2)]+[str(x) for x in [16.5, 17.0, 17.5, 18.0]]
print(valori_lk)
f_res = []
risonanze = []
plt.figure(figsize=(10, 6))
colormap = cm.get_cmap('plasma')
n_sets = len(valori_lk)
for i, lk in enumerate(valori_lk):
    df = estrai_dataset(file_csv, lk)
    x = df['FREQUENCY (GHz)'].values
    y = df[' DB[S21]-2D_3rd_resonator'].values
    
    x0_guess = x[np.argmin(y)]  # Il minimo grezzo della curva
    y0_guess = np.max(y)        # Il valore massimo (lontano dalla risonanza)
    A_guess = y0_guess - np.min(y) # La profondità approssimata
    #if x0_guess > 17 :
    #    x0_guess = 15.8
    #    A_guess = -0.689
    gamma_guess = 0.01          # Stima della larghezza
    
    p0 = [y0_guess, A_guess, x0_guess, gamma_guess]
    colore = colormap(i / (n_sets - 1)) if n_sets > 1 else colormap(0)
    # Esegui il fit non linearef

    try:
        par, pcov = curve_fit(lorentziana_inv, x, y, p0=p0)

        par_err = np.sqrt(np.diag(pcov))

        f_risonanza = par[2] # x0 è il terzo parametro
        err_risonanza = par_err[2]

        f_res.append({'Lk': float(lk), 'f_res_GHz': f_risonanza, 'err_f_res': err_risonanza})
        risonanze.append(f_risonanza)
        # Plot dei dati originali e della curva fittata
        #plt.plot(x, y, label=f'Dati Lk={lk}', linestyle='--', alpha=0.4)
        plt.plot(x, lorentziana_inv(x, *par), 
                     label=f'Lk={lk} (Fr={f_risonanza:.4f} ± {err_risonanza:.4f} GHz)', color=colore, linewidth=2)
                 
    except Exception as e:
        print(f"Fit fallito per Lk={lk}: {e}")

# Personalizza e mostra il grafico
plt.xlabel('Frequency (GHz)')
plt.ylabel('S21 (dB)')
plt.title('Frequency response for different Lk values (1st RESONATOR)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid()
#plt.show()

# ==========================================
# SECONDA PARTE: FIT Fr vs Lk CON ERRORI
# ==========================================


def function(x,a, Lg):
    return a/np.sqrt(x+Lg)

Lk_values = np.array([entry['Lk'] for entry in f_res])
f_res_values = np.array([entry['f_res_GHz'] for entry in f_res])
f_res_errors = np.array([entry['err_f_res'] for entry in f_res])

a_guess = 20
Lg_guess = 3
p1 = [a_guess, Lg_guess]

par2, pcov2 = curve_fit(function, Lk_values, f_res_values, p0=p1, sigma=f_res_errors, absolute_sigma=True)
print(f"Fit parameters: a={par2[0]:.4f}, Lg={par2[1]:.4f}")
funct_par_err = np.sqrt(np.diag(pcov2))

# ==========================================
# STIMA DI Lk PER UNA FREQUENZA DI RISONANZA DATA (es. 7.5 GHz)
# ==========================================

def find_Lk_con_errore(f_target, par, pcov):
    a = par[0]
    Lg = par[1]
    
    # 1. Calcolo del valore nominale di Lk
    Lk = (a**2 / f_target**2) - Lg
    
    # 2. Calcolo delle derivate parziali per la propagazione
    dLk_da = 2 * a / (f_target**2)
    dLk_dLg = -1
    
    # 3. Estrazione dei termini dalla matrice di covarianza
    var_a = pcov[0, 0]      # Varianza di a (errore al quadrato di a)
    var_Lg = pcov[1, 1]     # Varianza di Lg (errore al quadrato di Lg)
    cov_a_Lg = pcov[0, 1]   # Covarianza tra a e Lg
    
    # 4. Formula completa della propagazione dell'errore (Varianza totale)
    var_Lk = (dLk_da**2 * var_a) + (dLk_dLg**2 * var_Lg) + (2 * dLk_da * dLk_dLg * cov_a_Lg)
    
    # L'incertezza finale è la radice quadrata della varianza
    errore_Lk = np.sqrt(var_Lk)
    
    return Lk, errore_Lk

f_target = 7.99294
Lk_target, Lk_target_err = find_Lk_con_errore(f_target, par2, pcov2)
print(f"Valore di Lk per f_res={f_target} GHz: {Lk_target:.4f} ± {Lk_target_err:.4f} nH")

plt.figure(figsize=(10, 6))

plt.errorbar(Lk_values, f_res_values, yerr=f_res_errors, fmt='o', 
             color='black', label='Data from simulations', markersize=4)

# 2. Plot della curva di fit continua
virtual_Lk = np.linspace(min(Lk_values) - 0.5, max(Lk_values) + 1.0, 500)
curva_fit = function(virtual_Lk, *par2)
plt.plot(virtual_Lk, curva_fit, color='blue', label='Fit', zorder=2)

# 3. Disegniamo le linee di estrazione (il "mirino")
# Linea orizzontale da sinistra fino alla curva
plt.hlines(y=f_target, xmin=plt.xlim()[0], xmax=Lk_target, 
           color='red', linestyle='--', alpha=0.7)

# Linea verticale dalla curva in giù
plt.vlines(x=Lk_target, ymin=plt.ylim()[0], ymax=f_target, 
           color='red', linestyle='--', alpha=0.7)

# 4. Evidenziamo il punto bersaglio e il suo errore ORIZZONTALE
# (Usiamo xerr perché l'incertezza calcolata ora è su Lk, asse x)
plt.errorbar(Lk_target, f_target, xerr=Lk_target_err, fmt='rs', 
             markersize=6, ecolor='red', capsize=5, 
             label='Target (7.5 GHz)', zorder=4)

# 5. Box di annotazione elegante con il risultato
testo_risultato = f"Kinetic inductance estimated:\n$L_k = {Lk_target:.4f} \pm {Lk_target_err:.4f}$ nH"
plt.annotate(testo_risultato,
             xy=(Lk_target, f_target), 
             xytext=(Lk_target , f_target + 1.5), # Sposta il testo un po' in alto a destra
             fontsize=11, 
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9),
             zorder=5)

# Stile e formattazione finale
plt.xlabel('Kinetic inductance $L_k$ (nH)', fontsize=12)
plt.ylabel('Resonance frequency $f_{res}$ (GHz)', fontsize=12)
plt.title(f'Estimation of Kinetic Inductance for $f_{{res}} = {f_target} GHz$', fontsize=14)
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)

# Regoliamo i limiti del grafico per far entrare bene il testo e le linee
plt.xlim(min(Lk_values) - 0.2, max(Lk_values) + 1.5)
plt.ylim(min(f_res_values) - 0.2, max(f_res_values) + 0.3)

plt.tight_layout()
plt.show()