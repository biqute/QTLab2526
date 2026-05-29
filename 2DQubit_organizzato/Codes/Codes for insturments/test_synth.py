from typing import Literal
import sys

import matplotlib
sys.path.append("../classes")
from synth import class_SYNTH
from classes2 import VNA
import serial
import serial.tools.list_ports
import time
import numpy as np
import matplotlib.pyplot as plt

ports = serial.tools.list_ports.comports()
for p in ports:
    print(p.device)

#porte e ip
port = "COM13"
ip_VNA = '193.206.156.3'
nome_file = "PROVA.npz"
my_LO = class_SYNTH(name = port)
my_vna = VNA( ip_VNA)
print(my_LO.get_IDN())
print(my_vna.get_IDN())
my_LO.turn_on()

# inizializzare VNA
f_center = 7.41e9
span = 0.5e9
my_vna.set_freq_center(f_center, span)
f_start = f_center-(span/2)
f_stop = f_center+(span/2)
points = 4000
my_vna.set_points(points)
freqs = np.linspace(f_start, f_stop, points)

#acquisizione dati, unica cosa che varia è la frequenza del sintetizzatore
lista_freq_LO = []
lista_dati = []
for i in range(5):
    f = 7.2e9 + i*100e6
    my_LO.set_freq(f)
    lista_freq_LO.append(my_LO.get_freq())
    time.sleep(2)
## inizializzare bene VNA, non salva bene i dati
    real, imag = my_vna.get_data("S21")
    my_vna.save_vna_data2(nome_file, freqs, real, imag)

    # plot grezzo dei dati acquisiti
    data = np.load(nome_file, allow_pickle=True)

    # metodo di lettura dati adattatati al codice resonator_fit
    struttura = data['0']
    freqs = struttura['freq']
    mag = struttura['signal']
    phase = struttura['phase']
    # -----------------------------------------------------
    dati_completi = np.column_stack((freqs, mag, phase))

    lista_dati.append(dati_completi)
    time.sleep(5)
    
print("Acquisizione completata")
print("Frequenze del sintetizzatore:", lista_freq_LO)
print(lista_dati)

for i in range(len(lista_freq_LO)):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(lista_dati[i][:,0] / 1e9, lista_dati[i][:,1], '.', markersize=2, color='b')
    ax1.set_title('Ampiezza (Magnitude)')
    ax1.set_xlabel('Frequenza (GHz)')
    ax1.set_ylabel('|S21|')
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2.plot(lista_dati[i][:,0] / 1e9, np.unwrap(lista_dati[i][:,2]), '.', markersize=2, color='r')
    ax2.set_title('Fase (Phase unwrapped)')
    ax2.set_xlabel('Frequenza (GHz)')
    ax2.set_ylabel('Fase (Radianti)')
    ax2.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()