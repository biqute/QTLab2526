import numpy as np
import pyvisa
from SDG import SDG

test_frequenza = SDG(ip_address ='192.168.40.15') #pass the ip as a string
a = test_frequenza.get_value(1, 'peri')
print(a)