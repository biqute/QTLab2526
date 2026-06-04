from typing import Literal
import sys

import matplotlib
sys.path.append("../classes")
from SYNTH import class_SYNTH
from VNA import VNA
import serial
import serial.tools.list_ports
import time
import numpy as np
import matplotlib.pyplot as plt

ports = serial.tools.list_ports.comports()
for p in ports:
    print(p.device)

#porte e ip
port = "COM14"
ip_VNA = '193.206.156.3'
#nome_file = "PROVA.npz"
my_LO = class_SYNTH(name = port)
#my_vna = VNA( ip_VNA)
print(my_LO.get_IDN())
#print(my_vna.get_IDN())

my_LO.turn_off()



#'''
my_LO.turn_on()
my_LO.set_pow(16)
my_LO.set_freq(5.62476e9)
#my_LO.set_freq(4.62476e9)
time.sleep(250)
#'''
#freq_list = np.arange(5.5e9, 5.7e9, 1e6) #
#for f in freq_list:
    #my_LO.set_freq(f)
    #lista_freq_LO.append(my_LO.get_freq())
    #time.sleep(2)
## inizializzare bene VNA, non salva bene i dati

    
#my_LO.turn_off()

