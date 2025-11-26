import sys
sys.path.append("../classes")
from VNA import VNA
from data import Data
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
    
ip = '193.206.156.99'

f_min = 1e9
f_max = 9e9
f_central = 8.6420e9
f_span = 0.1e9
n_points = 1001
n_means = 30
power = 0 #dBm
ifband = 10000

n_misura = "short_2"
data_file = "data_cable_" + n_misura
save_as = "cable_att_" + n_misura

Sij = "S21"

try:
    print(f"Connecting to VNA with ip =  {ip}...")
    vna = VNA(ip)
    print("Connection completed.")

    # 1. Identificazione
    print("VNA ID:")
    vna.get_IDN()

    # 2. Configurazione della Misura
    #vna.set_freq_span(f_central, f_span)
    vna.set_freq_limits(f_min,f_max)
    vna.set_sweep_points(n_points)
    vna.set_n_means(n_means)
    vna.set_ifband(ifband)
    vna.set_power(power)

    freq = np.array(vna.get_freq())/1e9
    powe = vna.get_dbm()
    I, Q = np.array(vna.get_S_parameters())
    amp = 10*np.log10(I**2+Q**2)
    
    data = Data(freq/1e9, I, Q)
    data.save_txt(file_to_save=data_file
                  #, commento="freq, I e Q"
                  )
    
    # Disegno
    fig, ax = plt.subplots()
    ax.set_title(f"Ampiezza {Sij}")
    ax.set_xlabel("Frequenza (GHz)")        
    ax.set_ylabel("Ampiezza (dBm)")
    ax.plot(freq, amp)
        
    plt.show()
    save_as+=".pdf"
    fig.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")

except pyvisa.errors.VisaIOError:
    print(f"\nERRORE: Impossibile connettersi al VNA ({ip}).")
    print("Controlla l'indirizzo IP, la connessione di rete e che il VNA sia acceso.")
except Exception as e:
        print(f"\nSi è verificato un errore: {e}")
