import sys; sys.path.append("../classes")
from VNA import VNA
import matplotlib.pyplot as plt
import numpy as np
    
ip = "192.168.1.100"
f_min = 4e9
f_max = 4.19e9
npoints = 401

try:
    print(f"Connecting to VNA with ip =  {ip}...")
    vna = VNA(ip)
    print("Connection completed.")

    # 1. Identificazione
    print("VNA ID:")
    vna.get_IDN()

    # 2. Configurazione della Misura
    vna.set_freq_limits(min_freq=f_min, max_freq=f_max)
    vna.set_power(power_dbm=-10)
    vna.set_sweep_points(num=npoints)
    
    vna.save_data(Sij="S21", filename="misura_S21_run1")
    print("Misura completata.")

except pyvisa.errors.VisaIOError:
    print(f"\nERRORE: Impossibile connettersi al VNA ({ip}).")
    print("Controlla l'indirizzo IP, la connessione di rete e che il VNA sia acceso.")
except Exception as e:
        print(f"\nSi è verificato un errore: {e}")
