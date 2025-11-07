import sys
sys.path.append("../classes")
from VNA import VNA
from data import Data
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
    
ip = "193.206.156.99"

f_min = 4.025e9
f_max = 4.1e9
npoints = 1001
n = 10
data_file = "misura_S21"
output_file = "risonanza_test"
power = 0

try:
    print(f"Connecting to VNA with ip =  {ip}...")
    vna = VNA(ip)
    print("Connection completed.")

    # 1. Identificazione
    print("VNA ID:")
    vna.get_IDN()

    # 2. Configurazione della Misura
    vna.set_freq_limits(min_freq=f_min, max_freq=f_max)
    vna.set_power(power_dbm=power)
    vna.set_sweep_points(num=npoints)
    vna.set_average(n)
    
    vna.save_data(Sij="S21", filename=data_file)
    print("Misura completata.")
    
    d = Data()
    d.plot(file=data_file, save_as=output_file+".pdf")  # legge ../data/misura_001.txt e lo plott
    d.plot()

except pyvisa.errors.VisaIOError:
    print(f"\nERRORE: Impossibile connettersi al VNA ({ip}).")
    print("Controlla l'indirizzo IP, la connessione di rete e che il VNA sia acceso.")
except Exception as e:
        print(f"\nSi è verificato un errore: {e}")
