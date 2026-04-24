import numpy as np
import time
import pyvisa
from classes2 import LO
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for p in ports:
    print(p.device)


my_lo = LO(name='COM9')
my_lo.turn_off()
my_lo.set_freq(5000000000)
my_lo.set_pow(15)
#my_lo.turn_on()





