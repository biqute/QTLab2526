import numpy as np
import pyvisa
from class_vna import VNA

my_class = VNA(ip_address ='193.206.156.99') #pass the ip as a string
print(my_class.set_points(1000))