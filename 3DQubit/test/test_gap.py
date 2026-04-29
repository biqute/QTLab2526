import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Aggiunta path per trovare la classe
sys.path.append("../classes")
from GapFinder import GapFinder 

# --- CONFIGURAZIONE ---
# Inserisci qui il percorso corretto del tuo file reale
path_to_file = "../T_dep_results/revQ_vs_Temperature.txt"

# --- ESECUZIONE ---

# Inizializzazione della classe con i dati reali
# omega: frequenza di risonanza, alpha: kinetic inductance fraction
finder = GapFinder(
    filename=path_to_file, 
    omega=7.49e9, 
    alpha=0.1, # found from Sonnet simulation
    fit_type='standard'
)

# Impostiamo il limite di temperatura per il fit (es. 400 mK)
finder.set_T_limit(400)

# Esecuzione del Fit (interpolazione fisica)
minuit_result = finder.fit()

# --- OUTPUT RISULTATI ---
if minuit_result.valid:
    print(f"\n FIT completato con successo")
    print("-" * 40)
    val = minuit_result.values
    err = minuit_result.errors
    
    print(f"Gap Energetico (delta0): {val['delta0']:.4f} ± {err['delta0']:.4f}")
    print(f"Perdite Residue (q0):    {val['q0']:.2e} ± {err['q0']:.2e}")
    print("-" * 40)
    print(f"FCN (Chi-quadro): {minuit_result.fval:.4f}")
else:
    print("IL FIT È FALLITO")

# --- PLOTTING ---
plt.figure(figsize=(10, 6))

# Visualizziamo i dati reali caricati
# Se non hai errori nel file, verranno mostrati con errore standard = 1.0 (se hai modificato la classe)
plt.plot(finder._temps, finder._q_inv, 'ko', markersize=5, label='Dati Sperimentali (Reali)')

# Se il fit è valido, disegniamo la curva interpolante
if minuit_result.valid:
    t_plot = np.linspace(min(finder._temps), max(finder._temps), 100)
    y_plot = [finder._fit_function(t, *minuit_result.values) for t in t_plot]
    plt.plot(t_plot, y_plot, 'r-', linewidth=2, label='Modello Mattis-Bardeen')

plt.title(f'Analisi Gap Energetico - {os.path.basename(path_to_file)}')
plt.xlabel('Temperatura [mK]')
plt.ylabel('1/Q (Losses)')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)

# Mostriamo il grafico
plt.show()