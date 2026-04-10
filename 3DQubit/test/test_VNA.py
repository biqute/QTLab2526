import sys
sys.path.append("../classes")
from VNA import VNA
from data import Data
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
    
ip = '193.206.156.3'

f_min = 7.36e9
f_max = 7.54e9
f_central = 7.489429e9
f_span = 45e6
n_points = 10001
n_means = 1
power = 0
ifband = 1e3


n_misura = "775mK"
data_file = "../T_dep/"+"2_MKID_resonance_" + n_misura
output_file = "../T_dep/"+"2_MKID_plot_" +  n_misura

Sij = "S21"

try:
    print(f"Connecting to VNA with ip =  {ip}...")
    vna = VNA(ip)
    print("Connection completed.")

    # 1. Identificazione
    print("VNA ID:")
    vna.get_IDN()

    # 2. Configurazione della Misura
    vna.set_freq_span(f_central, f_span)
    #vna.set_freq_limits(f_min,f_max)
    vna.set_sweep_points(n_points)
    vna.set_n_means(n_means)
    vna.set_ifband(ifband)
    vna.set_power(power)
    #vna._VNA.write("INIT:CONT OFF") # Disabilita lo sweep continuo
    #vna._VNA.write("INIT:IMM")
    #phi = np.unwrap(vna.get_phase())
    
    
    #vna.perform_single_sweep(timeout=60000)
    phi = vna.get_phase()

    freq = vna.get_freq()
    powe = vna.get_dbm()
    I, Q = vna.get_S_parameters()
    #data = Data()
    #data.plot(freq, powe)
    #data.plot(freq, phi)

    #data = Data(freq, I, Q)
    #data.save_txt(file_to_save=data_file
    #              #, commento="freq, I e Q"
    #              )
    
    import numpy as np

    # Raggruppa le variabili in colonne
    dati_completi = np.column_stack((freq, I, Q))

    # Salva direttamente nel file txt
    np.savetxt(data_file+".txt", dati_completi, delimiter="\t", comments="")

    # Creating window (fig) with 2 axes (ax1, ax2) 
    fig, (ax1, ax2) = plt.subplots(
        nrows=1,        # 1 riga
        ncols=2,        # 2 colonne
        figsize=(14, 6) # Dimensioni della finestra
    )

    # --- Plot 1: Ampiezza ---
    ax1.plot(freq, powe, color='blue')
    ax1.set_title(f"Ampiezza {Sij}")
    ax1.set_xlabel("Frequenza (Hz)")
    ax1.set_ylabel("Ampiezza (dBm)")
    ax1.grid(True)

    # --- Plot 2: Fase ---
    ax2.plot(freq, phi, color='red')
    ax2.set_title(f"Fase {Sij}")
    ax2.set_xlabel("Frequenza (Hz)")
    ax2.set_ylabel("Fase (rad)")
    ax2.grid(True)

    # Mostra la finestra con entrambi i grafici
    plt.suptitle(f"Misura VNA ({Sij})") # Titolo generale
    plt.tight_layout() # Ottimizza gli spazi
    plt.show()

except pyvisa.errors.VisaIOError:
    print(f"\nERRORE: Impossibile connettersi al VNA ({ip}).")
    print("Controlla l'indirizzo IP, la connessione di rete e che il VNA sia acceso.")
except Exception as e:
        print(f"\nSi è verificato un errore: {e}")
