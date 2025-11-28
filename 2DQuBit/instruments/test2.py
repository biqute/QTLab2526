import numpy as np
import pyvisa
from classes import SDG, TDS, VNA
import matplotlib.pyplot as plt

my_sdg = SDG(ip_address ='193.206.156.10')
my_sdg.get_IDN()
my_sdg.singleshot(1, 1000, 6, 0, 0, 60)
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
plt.show()

