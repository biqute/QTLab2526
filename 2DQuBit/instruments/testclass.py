import numpy as np
import pyvisa
from classes import SDG, TDS, VNA
from gaussian import SDG_new
import matplotlib.pyplot as plt


my_vna = VNA(ip_address ='193.206.156.25') #pass the ip as a string 
my_vna.get_IDN()

'''my_sdg = SDG(ip_address ='193.206.156.10')
#my_sdg.set_formwave(1,'SINE')
#my_sdg.set_all(1, 4E3, 15, 0, 0)
#my_sdg.set_mod_freq(1, 100)
#my_sdg.modulation('on', 100)

my_sdg.gaussian_pulse(1, 1000, 6, 0, 0, 100)
#my_sdg.set_formwave(2, 'ARB', 5)
#my_sdg.set_all(2, 1, 6, 3 , 0)

tds = TDS('3')




sta = 0
sto = 5000
X = tds.acquisition(ch = 1, start = sta , stop = sto)
print(max(X['data']), min(X['data']))
x = np.linspace(0, (sto-sta)/X['sample_rate'], len(X['data']))
y = np.zeros(len(x))
fig, ax = plt.subplots(figsize=(10,5))
plt.plot(x, X['data'])
plt.plot(x, y)
plt.show()'''