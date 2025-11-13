import sys
sys.path.append("../classes")
from VNA import VNA
from data import Data
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
    
ip = '193.206.156.99'

f_min = 4.025e9
f_max = 4.1e9
f_central = 4.05e9
f_span = 0.05e9
n_points = 801
n_means = 10
power = -15
ifband = 1000
data_file = "misura_S21"
output_file = "risonanza_test"


try:
    print(f"Connecting to VNA with ip =  {ip}...")
    vna = VNA(ip)
    print("Connection completed.")

    # 1. Identificazione
    print("VNA ID:")
    vna.get_IDN()

    # 2. Configurazione della Misura
    vna.set_freq_span(f_central, f_span)
    vna.set_sweep_points(n_points)
    vna.set_n_means(n_means)
    vna.set_ifband(1000)
    vna.set_power(power)
    
    phi = vna.get_phase()
    freq = vna.get_freq()
    powe = vna.get_dbm()
    I, Q = vna.get_S_parameters("S21")
    data = Data()
    data.plot(freq, powe)
    data.plot(freq, phi)

except pyvisa.errors.VisaIOError:
    print(f"\nERRORE: Impossibile connettersi al VNA ({ip}).")
    print("Controlla l'indirizzo IP, la connessione di rete e che il VNA sia acceso.")
except Exception as e:
        print(f"\nSi è verificato un errore: {e}")
