import numpy as np
import pyvisa
import matplotlib.pyplot as plt
from VNA.VNA_class import VNA

# ==============================
# Connessione al VNA
# ==============================
test_frequenza = VNA(ip_address_string='193.206.156.99')

# ==============================
# Lettura delle frequenze
# ==============================
frequenze = test_frequenza.read_frequency_data()

# ==============================
# Scelta del parametro Sij
# ==============================
print("Seleziona il parametro di scattering:")
print("1: S11")
print("2: S21")
print("3: S12")
print("4: S22")
selezione = input("Inserisci il numero (1-4): ")

s_map = {"1": "S11", "2": "S21", "3": "S12", "4": "S22"}
sij = s_map.get(selezione, "S11")
print(f"Selezionato: {sij}")

# ==============================
# Lettura dei dati Sij
# ==============================
tau = 15e-9
q = -609

s_data = test_frequenza.read_data(sij)
s_real = np.array(s_data["real"])
s_imag = np.array(s_data["imag"])
s_magnitude = np.sqrt(s_real**2 + s_imag**2)
s_phase = np.arctan2(s_imag, s_real)
s_phase_unwrapped = np.unwrap(s_phase)

param = tau*frequenze + q

# ==============================
# Grafico: fase in funzione dell'ampiezza
# ==============================
# Traccia la fase del parametro scelto
plt.figure(figsize=(10, 6))
plt.plot(frequenze, s_phase_unwrapped/param, label=f"Fase {selezione}", color='orange')
plt.xlabel('Frequenza (Hz)')
plt.ylabel(f'Fase (radianti)')
plt.title(f'Fase di S21 in funzione della frequenza')
plt.grid(True)
plt.legend()
plt.show()

