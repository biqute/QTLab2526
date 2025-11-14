import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

TAU =89.29e-09 + 400 * 1.0001000100010001e-07
# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})


def guess_delay(f_data,z_data):
        phase2 = np.unwrap(np.angle(z_data))
        gradient, intercept, r_value, p_value, std_err = stats.linregress(f_data,phase2)
        return gradient*(-1.)/(np.pi*2.)
#N = 15000;

# Carica i dati dal file
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = (data['0']['phase'])


S21 = signal * np.exp(+1j * phase) 
phase = np.unwrap(np.angle(S21)) 
# Sintassi: np.polyfit(dati_x, dati_y, grado_del_polinomio)
# L'output è un array di coefficienti [m, b]
coefficients = np.polyfit(frequencies , phase, 1)

tau = guess_delay(frequencies, S21)
print("tau_guess:", tau)
b_intercept = coefficients[1]
T_B = 1/(frequencies.max()-frequencies.min())
tau_true = tau 

print("T_B:", T_B)
print("tau :", tau)

# --- 3. Creare la retta di fit per il grafico ---
# np.poly1d è una comoda funzione che trasforma
# i coefficienti in una funzione che possiamo chiamare.
#fit_function = np.poly1d(coefficients)

# Calcoliamo i valori Y della retta di fit per ogni X
#y_fit = fit_function(frequencies)

# --- Grafico: Fase vs Frequenza ---
plt.figure(figsize=(10, 5))
plt.plot(S21.real, S21.imag,
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
