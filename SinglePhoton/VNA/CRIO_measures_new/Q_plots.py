import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE ---
file_path = "quality_factors.csv"         # Inserisci il nome corretto del tuo file
colonna_da_plottare = "R1"     # Scegli la colonna: "R1", "R2", "R3", "R4" o "R5"

# --- LETTURA E PULIZIA DATI ---
# sep=';' imposta il separatore corretto
# skipinitialspace=True ignora gli spazi extra dopo il punto e virgola
df = pd.read_csv(file_path, sep=';', skipinitialspace=True)

# Rimuoviamo eventuali colonne fantasma create dai ';;' a fine riga
df = df.dropna(axis=1, how='all')

# Puliamo i nomi delle colonne da eventuali spazi invisibili accidentali
df.columns = df.columns.str.strip()

# Controlliamo che la colonna scelta esista
if colonna_da_plottare not in df.columns:
    print(f"Errore: La colonna '{colonna_da_plottare}' non esiste.")
    print(f"Colonne disponibili: {list(df.columns)}")
else:
    # --- ESTRAZIONE DATI ---
    T = df['T(mK)']
    R = df[colonna_da_plottare]

    # --- PLOT ---
    plt.figure(figsize=(8, 6))
    
    # Plottiamo i punti connessi da linee. marker='o' mette i pallini sui punti dati
    plt.plot(T, R, marker='o', linestyle='-', color='b', label=colonna_da_plottare)

    # Formattazione del grafico
    plt.title(f'Andamento di {colonna_da_plottare} in funzione della Temperatura', fontsize=14)
    plt.xlabel('Temperatura T (mK)', fontsize=12)
    plt.ylabel(f'Internal Quality Factor ({colonna_da_plottare})', fontsize=12)
    
    # Griglia e legenda
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    plt.tight_layout()

    # Mostra il risultato
    plt.show()