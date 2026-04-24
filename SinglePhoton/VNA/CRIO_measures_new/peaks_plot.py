import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# =========================================================
# IMPOSTAZIONI DELLE CARTELLE
# =========================================================
# Inserisci qui i percorsi relativi o assoluti delle 4 cartelle.
# Se esegui lo script dalla cartella "CRIO_measures_new", 
# i percorsi relativi dovrebbero essere simili a questi:
folder_base = "10mk"
folder_11_95 = "11_95mk"
folder_100  = "100mk"
folder_200  = "200mk"
folder_350  = "350mk"
folder_450  = "450mk"
folder_550  = "550mk"
folder_650  = "650mk"
folder_700  = "700mk"
folder_750  = "750mk"
folder_800  = "800mk"
folder_850  = "850mk"
folder_950  = "950mk"

# Mappiamo le etichette del grafico con il percorso completo dei file
file_dict = {
    "10 mk": os.path.join(folder_base, "picco3_big_new10mk.csv"),
    "11.95 mk": os.path.join(folder_11_95, "picco3_big_new.csv"),
    "100 mk": os.path.join(folder_100, "picco3_big_new100mk.csv"),
    "200 mk": os.path.join(folder_200, "picco3_big_new200mk.csv"),
    "350 mk": os.path.join(folder_350, "picco3_big_new350mk.csv"),
    "450 mk": os.path.join(folder_450, "picco3_big_new450mk.csv"),
    "550 mk": os.path.join(folder_550, "picco3_big_new550mk.csv"),
    "650 mk": os.path.join(folder_650, "picco3_big_new650mk.csv"),
    "700 mk": os.path.join(folder_700, "picco3_big_new700mk.csv"),
    "750 mk": os.path.join(folder_750, "picco3_big_new750mk.csv"),
    "800 mk": os.path.join(folder_800, "picco3_big_new800mk.csv"),
    "850 mk": os.path.join(folder_850, "picco3_big_new850mk.csv"),
    "950 mk": os.path.join(folder_950, "picco3_big_new950mk.csv")
}

# =========================================================
# CREAZIONE DEL GRAFICO
# =========================================================
plt.figure(figsize=(10, 6))

for label, file_path in file_dict.items():
    try:
        # Legge il file CSV
        data = pd.read_csv(file_path)
        #mask = (data["frequency"] >= 7.991e9)
        #data = data[mask]
        # Converte la frequenza in GHz per comodità di lettura sull'asse X
        freq_GHz = data['frequency'] / 1e9
        
        # Calcola l'ampiezza in scala logaritmica (dB)
        # Nota: La colonna 'Amplitude' nel tuo file è lineare.
        # Se preferisci graficare l'ampiezza lineare, usa semplicemente data['Amplitude']
        amp_dB = 20 * np.log10(data['Amplitude'])
        
        # Aggiunge i dati al grafico
        plt.plot(freq_GHz, amp_dB, label=label, marker='.', markersize=2, linestyle='-', alpha=0.8)
        
    except FileNotFoundError:
        print(f"ATTENZIONE: File non trovato al percorso -> {file_path}")

# Formattazione estetica del grafico
plt.title("Peak3")
plt.xlabel("Frequency (10e9 GHz)")
plt.ylabel("$|S_{21}|$ (dB)")
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(loc='best')
plt.tight_layout()

# Mostra la finestra interattiva
plt.show()