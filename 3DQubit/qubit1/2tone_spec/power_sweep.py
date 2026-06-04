from typing import Literal
import sys
import serial
import serial.tools.list_ports
import time
import numpy as np
import matplotlib.pyplot as plt

sys.path.append("../../classes")
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
my_LO.set_freq(5.62476e9) # Qubit's frequency

# --- Configurazione VNA per la Cavità (Readout) ---
f_min = 7.58e9
f_max = 7.586e9
n_points = 2001
n_means = 5
power = -20 # -20 servono per il power combiner piccolo
ifband = 100


my_vna.set_freq_limits(f_min, f_max)
my_vna.set_sweep_points(n_points)
my_vna.set_n_means(n_means)
my_vna.set_ifband(ifband)
my_vna.set_power(power)

data_file = "PowerSweep_data"

# Range di scansione del Qubit (Pump)
pow_list = np.arange(-15, 16, 1)  # da -20 a +16 dBm con passo di 2

# --- Prima di iniziare il ciclo FOR ---
I_list = []
Q_list = []

# Acquisiamo l'asse X (frequenze cavità) una volta sola, poiché i limiti del VNA sono fissi
freq_vna_X = my_vna.get_freq()  # Array 1D con 2001 elementi
    
my_vna.set_single_sweep_mode()
time.sleep(1) # Un secondo di assestamento
print("\n=== Inizio Spettroscopia a Due Toni ===")
for i, pow_drive in enumerate(pow_list):
    print(f"[{i+1}/{len(pow_list)}] Imposto Potenza drive = {pow_drive} dBm...")
    
    my_LO.set_pow(pow_drive)
    time.sleep(0.2) 
    print("   -> Avvio sweep e calcolo medie sul VNA...")
    my_vna.start_sweep()
    time.sleep(300)  # Attesa dello sweep delle medie
    
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
np.savez_compressed(f"{data_file}.npz", 
                    asse_x_vna = freq_vna_X,    # Asse X (Frequenza Lettura)
                    asse_y_pow = pow_list,   # Asse Y (Potenza Qubit)
                    I_data = I_matrix,          # Componente Reale
                    Q_data = Q_matrix)          # Componente Immaginaria

print("\n--> SUCCESS: Dati salvati in '{}'".format(f"{data_file}.npz"))
my_LO.turn_off()