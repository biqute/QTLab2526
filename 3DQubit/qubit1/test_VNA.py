import sys
import time
sys.path.append("../classes")
from VNA import VNA
from data import Data
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
    
ip = '193.206.156.3'

f_min = 7.576e9
f_max = 7.586e9

f_central = 7.5793e9
f_span = 3e6

n_points = 2001
n_means = 5
ifband = 100

Sij = "S21"

try:
    print(f"Connecting to VNA with ip =  {ip}...")
    vna = VNA(ip)
    print("Connection completed.")
    
    vna.set_freq_limits(f_min,f_max)
    vna.set_sweep_points(n_points)
    vna.set_n_means(n_means)
    vna.set_ifband(ifband)

    # 1. Identificazione
    print("VNA ID:")
    vna.get_IDN()

    pow_list = np.arange(-45, 3, 3) 
        
    freq = vna.get_freq()  
    vna.set_single_sweep_mode()
    
    for i, pow_vna in enumerate(pow_list):
        print(f"[{i+1}/{len(pow_list)}] Imposto Potenza drive = {pow_vna} dBm...")
        vna.set_power(pow_vna)
        time.sleep(0.2) 
        print("   -> Avvio sweep e calcolo medie sul VNA...")
        if(pow_vna <= -30):
            vna.set_n_means(5)
            vna.start_sweep()
            time.sleep(4.5*60)
        if(pow_vna <= -15 and pow_vna > -30):
            vna.set_n_means(2)
            vna.start_sweep()
            time.sleep(3*60)
        if(pow_vna > -15):
            vna.set_n_means(1)
            vna.start_sweep()
            time.sleep(2*60)
            
        I, Q = vna.get_S_parameters() # Array da 2001 elementi ciascuno
        # Raggruppa le variabili in colonne
        dati_completi = np.column_stack((freq, I, Q))
        
        n_misura = str(pow_vna)
        data_file = "Data/"+"power_"+n_misura 
        output_file = "Plots/plot_" +  n_misura + "dBm"
        np.savetxt(data_file+".txt", dati_completi, delimiter="\t", comments="")
        print(f"\nDati salvati in {data_file}.txt")
  
except pyvisa.errors.VisaIOError:
    print(f"\nERRORE: Impossibile connettersi al VNA ({ip}).")
    print("Controlla l'indirizzo IP, la connessione di rete e che il VNA sia acceso.")
except Exception as e:
        print(f"\nSi è verificato un errore: {e}")
