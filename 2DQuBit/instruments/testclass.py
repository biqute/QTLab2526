import numpy as np
import pyvisa
from classes import SDG
from gaussian import SDG_new


#my_vna = VNA(ip_address ='193.206.156.99') #pass the ip as a string
my_sdg = SDG_new(ip_address ='193.206.156.10')


my_sdg.set_formwave(1, 'ARB,INDEX,19')
my_sdg.modulation('off')
my_sdg.set_all(1,10,10,0,0)
print(my_sdg.get_value(1,'all'))