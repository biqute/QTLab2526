import numpy as np
import matplotlib.pyplot as plt

TAU = 4.009328078880438e-05
# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

#N = 15000;

# Carica i dati dal file
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])

S21 = signal * np.exp(1j * phase)*np.exp(-1j* 2*np.pi * TAU* frequencies)
phase = np.atan(S21.imag/S21.real)
# Sintassi: np.polyfit(dati_x, dati_y, grado_del_polinomio)
# L'output è un array di coefficienti [m, b]
#coefficients = np.polyfit(frequencies, phase, 1)

#tau = coefficients[0]/(2*np.pi)/1e9
#b_intercept = coefficients[1]

print("Fit Lineare (y = 2pi * tau x + b):")
#print("tau :", tau)

# --- 3. Creare la retta di fit per il grafico ---
# np.poly1d è una comoda funzione che trasforma
# i coefficienti in una funzione che possiamo chiamare.
#fit_function = np.poly1d(coefficients)

# Calcoliamo i valori Y della retta di fit per ogni X
#y_fit = fit_function(frequencies)

# --- Grafico: Fase vs Frequenza ---
plt.figure(figsize=(10, 5))
plt.plot(frequencies, phase,
         color='red',
         marker='.',         # Usa il 'punto' come marcatore
         linestyle='None',   # Non disegnare la linea che collega i punti
         markersize=1)       # Imposta la dimensione dei punti (puoi usare 1, 2, o anche 0.5)plt.title('Fase vs Frequenza', fontsize=16)
#plt.plot(frequencies, y_fit, '--', color='blue', label='Retta di Fit')
plt.xlabel(r"Frequency [GHz]", fontsize=12)
plt.ylabel(r"Phase [rad]", fontsize=12)
plt.grid(True)
plt.tight_layout()
plt.savefig('phase_fit.png')
print("Grafico Frequenza vs Fase salvato.")

plt.show()