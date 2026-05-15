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
                reading = True  # Inizia a salvare le righe
            else:
                if reading:
                    break  # Se abbiamo già letto il set, fermati al successivo "Lk="
            continue # Salta la riga specifica che contiene "Lk="
            
        if reading:
            dataset_lines.append(line)
            
    # Converte la lista di righe in un comodo DataFrame Pandas
    df = pd.read_csv(io.StringIO("".join(dataset_lines)))
    return df

def lorentziana_inv(x, y0, A, x0, gamma):
    return y0 - A * (gamma**2 / ((x - x0)**2 + gamma**2))

file_csv = 'L_geom_simul.csv'
valori_lk = [0]
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
                 label=f'Lk={lk} (Fr={f_risonanza:.4f} ± {err_risonanza:.4f} GHz)', color=colore)
                 
    except Exception as e:
        print(f"Fit fallito per Lk={lk}: {e}")

# Personalizza e mostra il grafico
plt.xlabel('Frequency (GHz)')
plt.ylabel('S21 (dB)')
plt.title('Frequency response with geometric inductance only (1st RESONATOR)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid()
plt.show()

f_res_values = np.array([entry['f_res_GHz'] for entry in f_res])
f_res_errors = np.array([entry['err_f_res'] for entry in f_res])

def calcola_alpha_diretto(f_real, err_f_real, f0, err_f0):

    # 1. Calcolo del valore nominale di alpha
    alpha = 1 - (f_real / f0)**2
    
    # 2. Derivate parziali
    dAlpha_df_reale = -2 * f_real / (f0**2)
    dAlpha_df0 = 2 * (f_real**2) / (f0**3)
    
    # 3. Propagazione degli errori (somma in quadratura)
    var_alpha = (dAlpha_df_reale * err_f_real)**2 + (dAlpha_df0 * err_f0)**2
    err_alpha = np.sqrt(var_alpha)
    
    return alpha, err_alpha

f_real_misurata = 7.992940    
err_f_real = 2.536749e-11

f0_simulata = f_res_values[0]       
err_f0 = f_res_errors[0]              

alpha_val, alpha_err = calcola_alpha_diretto(f_real_misurata, err_f_real, f0_simulata, err_f0)

print("--- METODO DIRETTO (f_real vs f0) ---")
print(f"Frequenza reale    : {f_real_misurata:.4f} ± {err_f_real:.4f} GHz")
print(f"Frequenza sim (f0) : {f0_simulata:.4f} ± {err_f0:.4f} GHz")
print(f"Frazione di Lk (α) : {alpha_val:.5f} ± {alpha_err:.5f}")
print(f"Alpha espresso in %: {alpha_val*100:.2f}% ± {alpha_err*100:.2f}%")
