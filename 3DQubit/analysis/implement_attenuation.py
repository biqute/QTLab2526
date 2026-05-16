import numpy as np

def choose_cable(cable_name):
    """
    Restituisce i parametri del fit in base al nome del cavo.
    L'ordine atteso dei parametri è: [a, b, c, d, phase, offset]
    """
    # Valori estratti dalla tabella (valori centrali, senza errore)
    if cable_name == "long_1":
        return [1.96, 0.258, -0.024, -3.724, 9.2, -2.322] 
    elif cable_name == "long_2":
        return [1.612, 0.188, 0.031, -1.70, -4.3, -1.72]
    elif cable_name == "short_1":
        return [0.541, 0.387, -0.027, -7.42, 24.5, -0.444]
    elif cable_name == "short_2":
        return [0.458, 0.58, 0.036, -10.389, 22.2, -0.297]
    else:
        raise ValueError(f"Nome cavo '{cable_name}' non riconosciuto. Usa 'long_1', 'long_2', 'short_1' o 'short_2'.")

def attenuation_func(x, p):
    """
    Calcola l'attenuazione fittata.
    x: Frequenza (stessa unità usata nel fit, es. Hz se data[:,0]*1e9)
    p: Array dei parametri del fit
    """
    return p[0] * np.exp(-p[1] * x) + p[2]*np.sin(p[3]*x+p[4]) + p[5]

def apply_two_cables_correction(data, cable1_name, cable2_name):
    """
    Prende in input i dati nel formato (N, 3) con colonne [Freq, I, Q]
    e restituisce i dati con l'attenuazione combinata di due cavi rimossa.
    """
    # Adatta la scala della frequenza come fatto in cable_attenuation.py
    f_fit_scale = data[:, 0] * 1e9 
    
    I = data[:, 1]
    Q = data[:, 2]
    
    # Estrai i parametri per entrambi i cavi
    p1 = choose_cable(cable1_name)
    p2 = choose_cable(cable2_name)
    
    # Valuta l'attenuazione (in dB) per ciascun cavo
    att_db_1 = attenuation_func(f_fit_scale, p1)
    att_db_2 = attenuation_func(f_fit_scale, p2)
    
    # L'attenuazione totale in dB è la somma delle singole attenuazioni
    att_db_total = att_db_1 + att_db_2
    
    # Converte l'attenuazione totale in dB a fattore di scala lineare (ampiezza)
    att_linear_total = 10 ** (att_db_total / 20.0)
    
    # De-attenua i dati grezzi
    I_corr = I / att_linear_total
    Q_corr = Q / att_linear_total
    
    # Ricostruisce l'array
    data_corrected = np.column_stack((data[:, 0], I_corr, Q_corr))
    
    return data_corrected

# ==========================================
# Esecuzione principale
# ==========================================
if __name__ == "__main__":
    input_base = "../data/cavity_13_642GHz"  # Sostituisci con il nome del file da correggere (senza estensione)
    
    # 1. Definisci i percorsi dei file
    input_filename = input_base + ".txt"  # Sostituisci con il percorso reale
    output_filename = input_base + "_corretta_2cavi.txt"
    
    # I cavi utilizzati ai capi della cavità
    cavo_in = "short_1" 
    cavo_out = "short_2"
    
    try:
        # 2. Carica i dati grezzi (Assumendo formato: Freq I Q separati da tabulazioni)
        raw_data = np.loadtxt(input_filename, delimiter="\t") 
        print(f"Dati caricati da {input_filename} con successo.")
        
        # 3. Applica la correzione per entrambi i cavi
        corrected_data = apply_two_cables_correction(raw_data, cavo_in, cavo_out)
        print(f"Correzione combinata per i cavi '{cavo_in}' e '{cavo_out}' applicata.")
        
        # 4. Salva i dati corretti nel nuovo file .txt
        np.savetxt(
            output_filename, 
            corrected_data, 
            fmt="%.8e", 
            delimiter="\t", 
            header="Frequency\tI_corrected\tQ_corrected",
            comments="# " 
        )
        print(f"Dati corretti salvati in {output_filename}.")
        
    except FileNotFoundError:
        print(f"ERRORE: Il file {input_filename} non è stato trovato.")
    except Exception as e:
        print(f"Si è verificato un errore inaspettato: {e}")