import matplotlib.pyplot as plt
import re

# Inizializziamo le variabili per contenere i dati
data = {}
current_lk = None
freqs = []
db_vals = []

# Leggiamo il file CSV
with open('Lk_tot.csv', 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        # Identifichiamo l'inizio di un nuovo blocco di dati tramite la dicitura "Lk="
        if "Lk=" in line:
            # Salviamo il blocco precedente se esiste
            if current_lk is not None and len(freqs) > 0:
                data[current_lk] = {'freq': freqs, 'db': db_vals}
                
            # Estraiamo il valore numerico di Lk
            match = re.search(r'Lk=([0-9.]+)', line)
            if match:
                current_lk = match.group(1)
            else:
                current_lk = "Sconosciuto"
            
            # Resettiamo le liste per il nuovo blocco
            freqs = []
            db_vals = []
            
        elif line.startswith('FREQUENCY'):
            # Saltiamo la riga delle intestazioni delle colonne
            continue
        else:
            # Estraiamo i valori di frequenza e DB
            try:
                parts = line.split(',')
                freq = float(parts[0])
                db = float(parts[1])
                freqs.append(freq)
                db_vals.append(db)
            except ValueError:
                pass

# Assicuriamoci di salvare l'ultimo blocco di dati
if current_lk is not None and len(freqs) > 0:
    data[current_lk] = {'freq': freqs, 'db': db_vals}

# Creazione del grafico
plt.figure(figsize=(12, 8))

# Plottiamo ogni set di dati
for lk, vals in data.items():
    plt.plot(vals['freq'], vals['db'], label=f'Lk={lk}')

# Personalizzazione del grafico
plt.xlabel('Frequenza (GHz)')
plt.ylabel('DB[Z33]')
plt.title('DB[Z33] vs Frequenza per diversi valori di Lk')

# Spostiamo la legenda fuori dal grafico per non coprire le curve
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
plt.tight_layout()

# Salviamo e mostriamo il risultato
plt.savefig('Lk_tot.png', dpi=300)
plt.show()