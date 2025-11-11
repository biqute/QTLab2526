import numpy as np
import pyvisa
import matplotlib.pyplot as plt
from VNA_class import VNA

# Crea un'istanza del VNA con l'indirizzo IP del dispositivo
test_frequenza = VNA(ip_address_string='193.206.156.99')

# Leggi i dati di frequenza
frequenze = test_frequenza.read_frequency_data()

# Chiedi all'utente di selezionare il parametro Sij (S11, S21, S12, S22)
print("Seleziona il parametro di scattering:")
print("1: S11")
print("2: S21")
print("3: S12")
print("4: S22")
selezione = input("Inserisci il numero (1-4): ")

# Funzione per leggere i dati Sij
def leggi_sij_dati(sij):
    s_data = test_frequenza.read_data(sij)
    s_real = s_data["real"]
    s_imag = s_data["imag"]
    s_magnitude = 10*np.log(np.sqrt(np.array(s_real)**2 + np.array(s_imag)**2))
    s_phase = np.arctan2(np.array(s_imag), np.array(s_real))
    s_phase_unwrapped = np.unwrap(s_phase)
    return s_real, s_imag, s_magnitude, s_phase_unwrapped,

# Esegui la selezione e leggi i dati Sij
if selezione == '1':
    print("Selezionato: S11")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S11")
elif selezione == '2':
    print("Selezionato: S21")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S21")
elif selezione == '3':
    print("Selezionato: S12")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S12")
elif selezione == '4':
    print("Selezionato: S22")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S22")
else:
    print("Scelta non valida. Utilizzerò S11 di default.")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S11")

# Traccia la magnitudine del parametro scelto
plt.figure(figsize=(10, 6))
plt.plot(frequenze, s_magnitude, label=f"Magnitudine {selezione}")
plt.xlabel('Frequenza (Hz)')
plt.ylabel('Magnitudine')
plt.title(f'Magnitudine di {selezione} in funzione della frequenza')
plt.grid(True)
plt.legend()
plt.show()

# Traccia la fase del parametro scelto
plt.figure(figsize=(10, 6))
plt.plot(frequenze, s_phase_unwrapped, label=f"Fase {selezione}", color='orange')
plt.xlabel('Frequenza (Hz)')
plt.ylabel(f'Fase {selezione} (radianti)')
plt.title(f'Fase di {selezione} in funzione della frequenza')
plt.grid(True)
plt.legend()
plt.show()

# Traccia il diagramma Re vs Im del parametro scelto
plt.figure(figsize=(10, 6))
plt.plot(s_real, s_imag, label=f"Re vs Im {selezione}", color='orange')
plt.xlabel(f'Re({selezione})')
plt.ylabel(f'Im({selezione})')
plt.title(f'Re vs Im di {selezione}')
plt.grid(True)
plt.legend()
plt.show()

