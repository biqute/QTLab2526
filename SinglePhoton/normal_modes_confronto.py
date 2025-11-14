import numpy as np
from scipy.special import jn_zeros, jnp_zeros
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

# --- PARAMETRI CAVITÀ ---
eps_r = 1.0006
mu_r = 1
c = 3e8
a = 26e-3       # raggio
d = 68.1e-3     # altezza
FMAX = 12e9

# --- NUMERO MASSIMO DI MODI ---
m_max = 3
n_max = 4
p_max = 4

# --- CARICAMENTO FILE CSV ---
nome_file = input("Percorso file CSV: ")
data = np.loadtxt(nome_file, delimiter=",", skiprows=1)  # skip intestazione
freq_exp = data[:,0]   # colonna frequenza
amp_exp  = data[:,3]   # colonna ampiezza

# --- TROVA TUTTI I PICCHI SPERIMENTALI ---
idx_peaks, _ = find_peaks(amp_exp, height=0)
freq_peaks = freq_exp[idx_peaks]
amp_peaks  = amp_exp[idx_peaks]

# --- SELEZIONA I 8 PICCHI PIU' ALTI ---
top_indices = np.argsort(amp_peaks)[-8:][::-1]
freq_peaks = freq_peaks[top_indices]
amp_peaks  = amp_peaks[top_indices]

# --- CALCOLO MODI TEORICI ---
modes = []

# TM modes
for m in range(m_max+1):
    zeros_tm = jn_zeros(m, n_max)
    for n in range(1, n_max+1):
        xmn = zeros_tm[n-1]
        for p in range(p_max+1):
            f = (c/(2*np.pi*np.sqrt(eps_r*mu_r))) * np.sqrt( (xmn/a)**2 + (p*np.pi/d)**2 )
            if f <= FMAX:
                modes.append(("TM", m, n, p, f))

# TE modes
for m in range(m_max+1):
    zeros_te = jnp_zeros(m, n_max)
    for n in range(1, n_max+1):
        xmn = zeros_te[n-1]
        for p in range(p_max+1):
            f = (c/(2*np.pi*np.sqrt(eps_r*mu_r))) * np.sqrt( (xmn/a)**2 + (p*np.pi/d)**2 )
            if f <= FMAX:
                modes.append(("TE", m, n, p, f))

# Ordina per frequenza crescente
modes_sorted = sorted(modes, key=lambda x: x[4])

# --- ASSOCIA PICCHI AI MODI TEORICI SENZA DUPLICATI ---
modes_available = modes_sorted.copy()
results_unique = []

for f_exp, a_exp in zip(freq_peaks, amp_peaks):
    if not modes_available:
        break
    
    mode_closest = min(modes_available, key=lambda x: abs(x[4]-f_exp))
    tipo, m, n, p, f_theor = mode_closest
    results_unique.append((tipo, m, n, p, f_theor, f_exp, a_exp))
    modes_available.remove(mode_closest)

# --- STAMPA RISULTATI ---
print("\nModo teorico   Frequenza teorica(GHz)   Frequenza misurata(GHz)   Ampiezza")
for r in results_unique:
    tipo, m, n, p, f_theor, f_exp, a_exp = r
    print(f"{tipo}_{m}{n}{p:1d}        {f_theor/1e9:8.4f}             {f_exp/1e9:8.4f}             {a_exp:.4f}")

# --- GRAFICO FREQUENZE SULLA STESSA LINEA Y ---
freq_peaks_GHz = freq_peaks / 1e9
f_theor_GHz = np.array([r[4] for r in results_unique]) / 1e9

plt.figure(figsize=(10,2))
plt.scatter(freq_peaks_GHz, [1]*len(freq_peaks_GHz), color='red', label='Picchi sperimentali', s=100)
plt.scatter(f_theor_GHz, [1]*len(f_theor_GHz), color='blue', marker='x', label='Modi teorici', s=100)

plt.xlabel('Frequenza (GHz)')
plt.yticks([])  # rimuove etichette y
plt.title('Confronto tra picchi sperimentali e modi teorici')
plt.legend()
plt.grid(axis='x')
plt.tight_layout()
plt.show()
