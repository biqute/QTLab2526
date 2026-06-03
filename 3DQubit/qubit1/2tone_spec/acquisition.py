from typing import Literal
import sys
import serial
import serial.tools.list_ports
import time
import numpy as np
import matplotlib.pyplot as plt

sys.path.append("../classes")
from SYNTH import class_SYNTH
from VNA import VNA

# --- Identificazione porte ---
ports = serial.tools.list_ports.comports()
for p in ports:
    print(f"Porta trovata: {p.device}")
    
port = "COM14"
ip_VNA = '193.206.156.3'

# --- Inizializzazione Strumenti ---
my_LO = class_SYNTH(name=port)
my_vna = VNA(ip_VNA)

print("IDN Synthesizer:", my_LO.get_IDN())
print("IDN VNA:", my_vna.get_IDN())

# Accendiamo il generatore di pump
my_LO.turn_on()
my_LO.set_pow(0) # Imposta una potenza iniziale (es. 0 dBm)

# --- Configurazione VNA per la Cavità (Readout) ---
f_min = 7.558e9
f_max = 7.608e9
n_points = 4001
n_means = 5
power = -17 # dBm
ifband = 100

my_vna.set_freq_limits(f_min, f_max)
my_vna.set_sweep_points(n_points)
my_vna.set_n_means(n_means)
my_vna.set_ifband(ifband)
my_vna.set_power(power)

data_file = "2tone_data"

# Range di scansione del Qubit (Pump)
freq_list = np.arange(5.6e9, 5.65e9, 1e6) 

# --- Prima di iniziare il ciclo FOR ---
I_list = []
Q_list = []

# Acquisiamo l'asse X (frequenze cavità) una volta sola, poiché i limiti del VNA sono fissi
freq_vna_X = my_vna.get_freq()  # Array 1D con 4001 elementi

print("\n=== Inizio Spettroscopia a Due Toni ===")
for i, f_drive in enumerate(freq_list):
    print(f"[{i+1}/{len(freq_list)}] Imposto f_drive = {f_drive/1e9:.4f} GHz...")
    
    my_LO.set_freq(f_drive)
    time.sleep(0.2) 
    
    my_vna.start_sweep() 
    time.sleep(500)  # Attesa dello sweep delle medie
    
    I, Q = my_vna.get_S_parameters() # Array da 4001 elementi ciascuno
    
    # Salviamo la riga intera nella nostra lista
    I_list.append(I)
    Q_list.append(Q)

# --- CONFIGURAZIONE STRUTTURA OTTIMALE (MATRICI 2D) ---
# Convertiamo le liste in matrici 2D reali. 
# Dimensioni risultanti: (Numero_f_drive, 4001) -> nel tuo caso (51, 4001)
I_matrix = np.array(I_list)
Q_matrix = np.array(Q_list)

# Salviamo gli assi indipendenti e le matrici Z in un unico file .npz
np.savez_compressed("spettroscopia_qubit.npz", 
                    asse_x_vna = freq_vna_X,    # Asse X (Frequenza Lettura)
                    asse_y_drive = freq_list,   # Asse Y (Frequenza Qubit)
                    I_data = I_matrix,          # Componente Reale
                    Q_data = Q_matrix)          # Componente Immaginaria

print("\n--> SUCCESS: Dati salvati in 'spettroscopia_qubit.npz'")
my_LO.turn_off()