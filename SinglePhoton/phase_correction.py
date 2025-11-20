import numpy as np

def correct_cable_delay(filename, tau, output):
    # Leggi il file (prova prima con virgole)
    try:
        data = np.genfromtxt(filename, delimiter=",", skip_header=1)
        if np.isnan(data).all():
            raise ValueError
    except:
        data = np.genfromtxt(filename, skip_header=1)

    freq = data[:, 0]
    Re = data[:, 1]
    Im = data[:, 2]
    phase = data[:, 4]
    amp = data[:, 3]

    # Applica la correzione a re e im
    phi = 2 * np.pi * freq * tau
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)



    Re_corr = Re * cos_phi - Im * sin_phi
    Im_corr = Re * sin_phi + Im * cos_phi
    phase_corr = np.arctan2(Im_corr, Re_corr)
    amp_corr = np.sqrt(Re_corr**2 + Im_corr**2)

    corrected = data.copy()
    corrected[:, 1] = Re_corr
    corrected[:, 2] = Im_corr
    corrected[:, 4] = phase_corr
    corrected[:, 3] = amp_corr 

    # Salva file corretto
    header = "freq,Re,Im,amp,phase"
    np.savetxt(output, corrected, delimiter=",", header=header)

    print(f"File corretto salvato come: {output}")


# ---------- COME USARLO ----------
if __name__ == "__main__":
    correct_cable_delay(
        filename="/Users/angelobassi/Desktop/QTLab2526/SinglePhoton/circle_fit/S21_data_50medie_hunger",  
        tau=12568e-11,                            
        output="S21_data_50medie_hunger_corretto"          
    )



# Esempio d’uso:
# correct_cable_delay("S21_data.csv", tau=1.23e-8)
