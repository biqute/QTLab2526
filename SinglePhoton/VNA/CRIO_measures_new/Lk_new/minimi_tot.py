import pandas as pd
import re

# Lista per salvare i risultati
data_mins = []
current_lk = None
freqs = []
db_vals = []

# Lettura del file
with open('Lk_tot.csv', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        # Nuovo blocco Lk
        if "Lk=" in line:
            # Calcola il minimo del blocco precedente
            if current_lk is not None and len(freqs) > 0:
                min_db = min(db_vals)
                min_idx = db_vals.index(min_db)
                min_freq = freqs[min_idx]
                data_mins.append({'Lk': float(current_lk), 'Frequenza_Minimo_GHz': min_freq, 'DB_Minimo': min_db})
                
            # Trova il nuovo valore di Lk
            match = re.search(r'Lk=([0-9.]+)', line)
            current_lk = match.group(1) if match else "Unknown"
            
            # Reset
            freqs = []
            db_vals = []
            
        elif line.startswith('FREQUENCY'):
            continue
        else:
            # Raccogli i dati di frequenza e db
            try:
                parts = line.split(',')
                freqs.append(float(parts[0]))
                db_vals.append(float(parts[1]))
            except ValueError:
                pass

# Calcola il minimo per l'ultimo blocco
if current_lk is not None and len(freqs) > 0:
    min_db = min(db_vals)
    min_idx = db_vals.index(min_db)
    min_freq = freqs[min_idx]
    data_mins.append({'Lk': float(current_lk), 'Frequenza_Minimo_GHz': min_freq, 'DB_Minimo': min_db})

# Crea un DataFrame Pandas, ordinalo per Lk e stampalo
df_min = pd.DataFrame(data_mins).sort_values(by='Lk')
print(df_min)

# Opzionale: Salva i risultati in un nuovo file CSV
df_min.to_csv('Frequenze_Minimi.csv', index=False)
print("\nRisultati salvati in 'Frequenze_Minimi.csv'")