import numpy as np
import pyvisa
import csv
from VNA_class import VNA

#193.206.156.99
# Crea un'istanza del VNA con l'indirizzo IP del dispositivo
test_frequenza = VNA(ip_address_string='193.206.156.99')

# Funzione per leggere i dati Sij
def leggi_sij_dati(sij):
    s_data = test_frequenza.read_data(sij)
    s_real = s_data["real"]
    s_imag = s_data["imag"]
    s_magnitude = np.sqrt(np.array(s_real)**2 + np.array(s_imag)**2)
    s_phase = np.arctan2(np.array(s_imag), np.array(s_real))
    s_phase_unwrapped = np.unwrap(s_phase)
    return s_real, s_imag, s_magnitude, s_phase_unwrapped

# Funzione per esportare i dati in CSV
def esporta_in_csv(sij, frequenze, s_real, s_imag, s_magnitude, s_phase_unwrapped):
    # Chiedi il nome del file
    file_name = input("Inserisci il nome del file CSV (es. dati_s11.csv): ").strip()
    
    # Scrivi i dati su un file CSV
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Scrivi l'intestazione del file CSV
        writer.writerow(["Frequenze (Hz)", "Parte Reale", "Parte Immaginaria", "Ampiezza", "Fase"])
        
        # Scrivi i dati
        for f, r, i, m, p in zip(frequenze, s_real, s_imag, s_magnitude, s_phase_unwrapped):
            writer.writerow([f, r, i, m, p])

    print(f"Dati esportati nel file {file_name}.")

# Chiedi all'utente di selezionare il parametro Sij (S11, S21, S12, S22)
print("Seleziona il parametro di scattering:")
print("1: S11")
print("2: S21")
print("3: S12")
print("4: S22")
selezione = input("Inserisci il numero (1-4): ")

# Esegui la selezione e leggi i dati Sij
if selezione == '1':
    print("Selezionato: S11")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S11")
    sij = "S11"
elif selezione == '2':
    print("Selezionato: S21")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S21")
    sij = "S21"
elif selezione == '3':
    print("Selezionato: S12")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S12")
    sij = "S12"
elif selezione == '4':
    print("Selezionato: S22")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S22")
    sij = "S22"
else:
    print("Scelta non valida. Utilizzerò S11 di default.")
    s_real, s_imag, s_magnitude, s_phase_unwrapped = leggi_sij_dati("S11")
    sij = "S11"

# Leggi i dati di frequenza
frequenze = test_frequenza.read_frequency_data()

# Chiedi se si desidera esportare i dati in un file CSV
export_csv = input("Vuoi esportare i dati su un file CSV? (si/no): ").strip().lower()

if export_csv == "si":
    esporta_in_csv(sij, frequenze, s_real, s_imag, s_magnitude, s_phase_unwrapped)
else:
    print("Non è stato esportato alcun dato in CSV.")
