import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
TAU =89.29e-09 + 400 * 1.0001000100010001e-07
# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

# Carica i dati dal file
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = (data['0']['phase'])

idx = np.argmin(signal)

frequencies = frequencies[idx+2500:-1]
phase = phase[idx+2500:-1]
signal = signal[idx+2500:-1]


S21 = signal * np.exp(+1j * phase) 
phase = np.unwrap(np.angle(S21)) 
# Sintassi: np.polyfit(dati_x, dati_y, grado_del_polinomio)
# L'output è un array di coefficienti [m, b]
coefficients = np.polyfit(frequencies , phase, 1)

tau = -coefficients[0]/(2*np.pi)
print("tau fit:", tau)
b_intercept = coefficients[1]


# --- 3. Creare la retta di fit per il grafico ---
# np.poly1d è una comoda funzione che trasforma
# i coefficienti in una funzione che possiamo chiamare.
fit_function = np.poly1d(coefficients)

# Calcoliamo i valori Y della retta di fit per ogni X
y_fit = fit_function(frequencies)

# --- Grafico: Fase vs Frequenza ---
plt.figure(figsize=(10, 5))
plt.plot(frequencies, phase,
         color='red',
         marker='.',         # Usa il 'punto' come marcatore
         linestyle='None',   # Non disegnare la linea che collega i punti
         markersize=1)       # Imposta la dimensione dei punti (puoi usare 1, 2, o anche 0.5)plt.title('Fase vs Frequenza', fontsize=16)
plt.plot(frequencies, y_fit, '--', color='blue', label='Retta di Fit')
plt.xlabel(r"Frequency [GHz]", fontsize=12)
plt.ylabel(r"Phase [rad]", fontsize=12)
plt.grid(True)
plt.tight_layout()
plt.savefig('phase_fit.png')
print("Grafico Frequenza vs Fase salvato.")

plt.show()
