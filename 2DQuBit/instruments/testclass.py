import numpy as np
import pyvisa
from classes import SDG, TDS
from gaussian import SDG_new
import matplotlib.pyplot as plt


#my_vna = VNA(ip_address ='193.206.156.99') #pass the ip as a string
'''
my_sdg = SDG_new(ip_address ='193.206.156.10')
my_sdg.set_formwave(1,'GAUS')
my_sdg.modulation('on')
my_sdg.set_all(1,10,5,0,0)
print(my_sdg.get_value(1,'all'))'''

tds = TDS('3')
print(tds.get_IDN())
tds.scale(ch = 1, scale = 2)
tds.res(ch = 1, res = 1e6)
sta = 0
sto = 5000
data_array, a, b= tds.acquisition(ch = 1, start = sta , stop = sto)
print(a*b*10)
print(data_array)
print(data_array, a)
x = np.linspace(0, (sto-sta)/a, len(data_array))
fig, ax = plt.subplots(figsize=(10,5))
plt.plot(x, data_array)
plt.show()