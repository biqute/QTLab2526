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

file_csv = 'Lk_all_1st_res.csv'
valori_lk = [str(float(i)) for i in range(0, 22, 2)]
print(valori_lk)
f_res = []
risonanze = []
plt.figure(figsize=(10, 6))
for lk in valori_lk:
    df = estrai_dataset(file_csv, lk)
    x = df['FREQUENCY (GHz)'].values
    y = df[' DB[S21]-2D_sonnet_new'].values
    
    x0_guess = x[np.argmin(y)]  # Il minimo grezzo della curva
    y0_guess = np.max(y)        # Il valore massimo (lontano dalla risonanza)
    A_guess = y0_guess - np.min(y) # La profondità approssimata
    gamma_guess = 0.01          # Stima della larghezza
    
    p0 = [y0_guess, A_guess, x0_guess, gamma_guess]
    
    # Esegui il fit non linearef

    try:
        par, _ = curve_fit(lorentziana_inv, x, y, p0=p0)
        
        f_risonanza = par[2] # x0 è il terzo parametro
        f_res.append({'Lk': float(lk), 'f_res_GHz': f_risonanza})
        risonanze.append(f_risonanza)
        # Plot dei dati originali e della curva fittata
        plt.plot(x, y, label=f'Dati Lk={lk}', alpha=0.4)
        plt.plot(x, lorentziana_inv(x, *par), '--', 
                 label=f'Fit Lk={lk} (fr={f_risonanza:.4f} GHz)')
                 
    except Exception as e:
        print(f"Fit fallito per Lk={lk}: {e}")

# Personalizza e mostra il grafico
plt.xlabel('Frequenza (GHz)')
plt.ylabel('S21 (dB)')
plt.title('Fit Lorentziano delle Risonanze')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
#plt.show()

def function(x,a, Lg):
    return a/np.sqrt(x+Lg)

Lk_values = [entry['Lk'] for entry in f_res]
f_res_values = [entry['f_res_GHz'] for entry in f_res]

a_guess = 1
Lg_guess = 0.1
p1 = [a_guess, Lg_guess]
par, _ = curve_fit(function, np.array(Lk_values), np.array(f_res_values), p1)

plt.figure(figsize=(8, 5))
plt.plot(Lk_values, f_res_values, marker='o')
plt.xlabel('Lk (nH)')
plt.plot(Lk_values, function(np.array(Lk_values), *par), '--', label='Fit f_res vs Lk')
plt.ylabel('Frequenza di Risonanza (GHz)')
plt.title('Frequenza di Risonanza vs Lk')
plt.grid()
plt.show()

print(f"Parametri del fit: a={par[0]:.4f}, Lg={par[1]:.4f} nH")

def find_Lk(x,a,Lg):
    return (a**2 / x**2) - Lg

print(f"Valore di Lk per f_res=7.5 GHz: {find_Lk(7.5, *par):.4f} nH")