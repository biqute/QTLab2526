import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import csv
import os

# ==============================
# Funzione per il fit della fase della risonanza
# ==============================
def phase_fit(f, theta0, Ql, fr):
    """
    Fase della risonanza:
    theta(f) = theta0 + 2 * arctan(2 * Ql * (1 - f / fr))
    """
    return theta0 + 2 * np.arctan(2 * Ql * (1 - f / fr))

# ==============================
# Funzione per leggere dati CSV
# ==============================
def leggi_dati_csv(nome_file):
    frequenze = []
    S21_complex = []
    ampiezze = []
    fasi = []
    
    if not os.path.isfile(nome_file):
        print(f"Errore: il file {nome_file} non esiste.")
        return None, None, None, None
    
    with open(nome_file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Salta intestazione
        for row in reader:
            frequenze.append(float(row[0]))
            S21_complex.append(float(row[1]) + 1j*float(row[2]))
            ampiezze.append(float(row[3]))
            fasi.append(float(row[4]))
    
    return np.array(frequenze), np.array(S21_complex), np.array(ampiezze), np.array(fasi)

# ==============================
# Lettura dati
# ==============================
nome_file = input("Inserisci il percorso del file CSV: ")
frequenze, S21_complex, ampiezze, fasi = leggi_dati_csv(nome_file)
if frequenze is None:
    raise SystemExit("Errore nella lettura del file.")

# ==============================
# Parametri del cerchio (dal fit algebraico)
# ==============================
xc = 0.00013393074676677603
yc = 0.00011052949028714455
r0 = 0.49797374462532246

# ==============================
# Fase della risonanza
# ==============================
phase_data = np.angle(S21_complex - (xc + 1j*yc))

# Stime iniziali per il fit della fase
theta0_init = 0.0
Ql_init = 5000.0
fr_init = frequenze[np.argmin(ampiezze)]
p0 = [theta0_init, Ql_init, fr_init]

params, _ = curve_fit(phase_fit, frequenze, phase_data, p0=p0)
theta0_opt, Ql_opt, fr_opt = params

print(f"\n=== Risultati fit fase ===")
print(f"Frequenza di risonanza fr = {fr_opt:.6f} Hz")
print(f"Quality factor totale Ql = {Ql_opt:.3f}")
print(f"Offset fase theta0 = {theta0_opt:.3f} rad")

# ==============================
# Calcolo punto off-resonance P'
# ==============================
beta = (theta0_opt + np.pi) % np.pi
P_prime = (xc + r0 * np.cos(beta)) + 1j * (yc + r0 * np.sin(beta))

a = np.abs(P_prime)
alpha = np.angle(P_prime)

print(f"\n=== Parametri globali ===")
print(f"Ampiezza globale a = {a:.6f}")
print(f"Fase globale alpha = {alpha:.6f} rad")

# ==============================
# Visualizzazione
# ==============================
plt.figure(figsize=(6,6))
plt.plot(S21_complex.real, S21_complex.imag, 'b.', label='Dati S21')
circle = plt.Circle((0,0), r0, color='r', fill=False, label='Cerchio fitato')
plt.gca().add_artist(circle)
plt.plot(P_prime.real, P_prime.imag, 'go', label="P' (off-resonance)")
plt.xlabel('Re[S21]')
plt.ylabel('Im[S21]')
plt.axis('equal')
plt.legend()
plt.grid(True)
plt.title('Determinazione a e alpha dal cerchio S21')
plt.show()
