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

def apply_cable_correction(data, cable_name):
    """
    Prende in input i dati nel formato (N, 3) con colonne [Freq, I, Q]
    e restituisce i dati con l'attenuazione del cavo rimossa.
    """
    # Adatta la scala della frequenza come fatto in cable_attenuation.py
    f_fit_scale = data[:, 0] * 1e9 
    
    I = data[:, 1]
    Q = data[:, 2]
    
    p = choose_cable(cable_name)
    
    # Valuta l'attenuazione (in dB) alle frequenze misurate
    att_db = attenuation_func(f_fit_scale, p)
    
    # Converte da dB a fattore di scala lineare (ampiezza)
    att_linear = 10 ** (att_db / 20.0)
    
    # De-attenua i dati grezzi
    I_corr = I / att_linear
    Q_corr = Q / att_linear
    
    # Ricostruisce l'array
    data_corrected = np.column_stack((data[:, 0], I_corr, Q_corr))
    
    return data_corrected

# ==========================================
# Esecuzione principale
# ==========================================
if __name__ == "__main__":
    input = "../data/cavity_7.29GHz"  # Sostituisci con il nome del file da correggere (senza estensione)
    # 1. Definisci i percorsi dei file e il nome del cavo
    input_filename = input + ".txt"  # Sostituisci con il percorso reale
    output_filename = input + "_corretta.txt"
    
    # Scegli uno tra: "long_1", "long_2", "short_1", "short_2"
    cavo_utilizzato = "short_1" 
    
    try:
        # 2. Carica i dati grezzi (Assumendo formato: Freq I Q separati da tabulazioni)
        raw_data = np.loadtxt(input_filename, delimiter="\t") 
        print(f"Dati caricati da {input_filename} con successo.")
        
        # 3. Applica la correzione
        corrected_data = apply_cable_correction(raw_data, cavo_utilizzato)
        print(f"Correzione per il cavo '{cavo_utilizzato}' applicata.")
        
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