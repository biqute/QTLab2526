from classes2 import VNA, MockVNA
import numpy as np
import matplotlib.pyplot as plt

my_vna = VNA(ip_address ='193.206.156.3') 
my_vna.get_IDN()


#my_vna.set_freq_minmax(f_start, f_stop)
f_center = 8.6435e9
span = 0.004e9
my_vna.set_freq_center(f_center, span)

f_start = f_center-(span/2)
f_stop = f_center+(span/2)
#f_start = 7.2e9
#f_stop = 8.8e9
points = 1200
my_vna.set_points(points)
my_vna.set_power(-5)
my_vna.set_sweep_time(0.00001)
my_vna.set_average(10)
freqs = np.linspace(f_start, f_stop, points)

'''
my_vna = MockVNA(f_center=5.1) # simulate a VNA with a resonance at 5.1 GHz
freqs = my_vna.get_frequencies()
'''

real, imag = my_vna.get_data("S21")
my_vna.save_vna_data2("PROVA.npz", freqs, real, imag)

# plot grezzo dei dati acquisiti
data = np.load('PROVA.npz', allow_pickle=True)

#freqs = data['freq']
#mag = data['signal']
#phase = data['phase']


# metodo alternativo -------------------------------
struttura = data['0']
# 2. Ora estrai le singole "colonne" (campi) dall'array strutturato
freqs = struttura['freq']
mag = struttura['signal']
phase = struttura['phase']
# -----------------------------------------------------
# 3. Ora la fase è un normale array 1D di numeri, e l'unwrap funzionerà alla perfezione!
phase_unwrapped = np.unwrap(phase)

print("Dati estratti e fase 'srotolata' con successo!")

# 3. Creazione figura
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(freqs / 1e9, mag, '.', markersize=2, color='b')
ax1.set_title('Ampiezza (Magnitude)')
ax1.set_xlabel('Frequenza (GHz)')
ax1.set_ylabel('|S21|')
ax1.grid(True, linestyle='--', alpha=0.7)

ax2.plot(freqs / 1e9, phase_unwrapped, '.', markersize=2, color='r')
ax2.set_title('Fase (Phase unwrapped)')
ax2.set_xlabel('Frequenza (GHz)')
ax2.set_ylabel('Fase (Radianti)')
ax2.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()