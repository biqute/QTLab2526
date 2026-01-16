import numpy as np
import pyvisa
from classes import LO

my_lo = LO(name='COM7')
print(my_lo.get_IDN())
my_lo.set_freq(5e9)
my_lo.turn_off()


