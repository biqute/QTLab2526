import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# 1. Caricamento dei dati dal CSV
# Forziamo esplicitamente la virgola come separatore per evitare problemi di parsing
df = pd.read_csv('Frequenze_Minimi.csv', sep=',')

# 2. Rimuoviamo eventuali spazi vuoti accidentali dai nomi delle colonne
df.columns = df.columns.str.strip()

print("Colonne rilevate nel file:", df.columns.tolist())

# 3. Estrazione degli array per il fit
Lk_data = df['Lk'].values
f0_data = df['Frequenza_Minimo_GHz'].values

Lk_data = np.insert(Lk_data, 0, 0.0)
f0_data = np.insert(f0_data, 0, 14.53)

# 4. Definizione del modello matematico (Equazione di Thomson per la frequenza di risonanza)
# Lk è la variabile indipendente, Lgeo e C sono i parametri da fittare
def res_freq(Lk, Lgeo, C):
    return 1.0 / (2 * np.pi * np.sqrt((Lgeo + Lk) * C))

# 5. Esecuzione del Fit Non Lineare
# p0 contiene le ipotesi iniziali per i parametri [Lgeo, C]
# bounds forza l'algoritmo a cercare solo valori positivi per evitare problemi (es. radici quadrate di numeri negativi)
popt, pcov = curve_fit(
    res_freq, 
    Lk_data, 
    f0_data, 
    p0=[5.0, 0.0001], 
    bounds=([0, 0], [np.inf, np.inf])
)

Lgeo_opt = popt[0]
C_opt = popt[1]

print(f"Parametri ottimali trovati:")
print(f"Lgeo = {Lgeo_opt:.4f}")
print(f"C    = {C_opt:.7f}")

# 6. Creazione e personalizzazione del grafico
plt.figure(figsize=(10, 6))

# Plot dei dati simulati/sperimentali (i minimi estratti)
plt.plot(Lk_data, f0_data, 'bo', label='Dati Estratti (Minimi)')

# Creazione di un array più denso di valori Lk per tracciare una curva fluida per il fit
Lk_fit = np.linspace(min(Lk_data), max(Lk_data), 100)
f0_fit = res_freq(Lk_fit, Lgeo_opt, C_opt)

# Plot della curva fittata con il modello matematico
plt.plot(Lk_fit, f0_fit, 'r-', label=f'Fit: $L_{{geo}}$={Lgeo_opt:.3f}, $C$={C_opt:.5f}')

# Etichette, titolo e legenda
plt.xlabel('$L_k$ (Induttanza Cinetica)')
plt.ylabel('Frequenza di Risonanza $f_0$ (GHz)')
plt.title('Fit della Frequenza di Risonanza')
plt.legend()
plt.grid(True)
plt.tight_layout()

f_target = 7.4922873822

# Calcolo inverso di Lk
Lk_estrapolato = (1.0 / ((2 * np.pi * f_target)**2 * C_opt)) - Lgeo_opt

print("\n--- ESTRAPOLAZIONE ---")
print(f"Frequenza Target: {f_target} GHz")
print(f"Valore stimato di Lk: {Lk_estrapolato:.4f}")

# Aggiungiamo il punto estrapolato al grafico con una stella verde
plt.plot(Lk_estrapolato, f_target, 'g*', markersize=15, 
         label=f'Target $f={f_target:.2f} \Rightarrow L_k={Lk_estrapolato:.2f}$')

# Aggiorniamo la legenda in modo che includa il nuovo punto
plt.legend()

# 7. Salvataggio dell'immagine e visualizzazione a schermo
plt.savefig('fit_frequenza_risonanza.png', dpi=300)
plt.show()