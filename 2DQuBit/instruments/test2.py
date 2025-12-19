import numpy as np
import pyvisa
from classes import SDG, TDS, VNA
import matplotlib.pyplot as plt
import warnings

my_sdg = SDG(ip_address ='193.206.156.10')
#par_gau = {'ampiezza': 1, 'frequenza': 10, 'media': 0, 'sigma': 1e-3}
sigma_ = 1e-3
interval = [-5*sigma_, +5*sigma_]
#sigma_ = 0.5
#intervals = [-7*sigma_, +7*sigma_]
my_sdg.upload_waveform(sigma_, name = 'singleshot', interval=interval)
my_sdg.manual_trig()
#my_sdg.set_samp(2.4e9)

#tds = TDS('3')
#tds.set_sample_rate(2.4e9)

'''sta = 0
sto = 5000
X = tds.acquisition(ch = 1, start = sta , stop = sto)
print(max(X['data']), min(X['data']))
x = np.linspace(0, (sto-sta)/X['sample_rate'], len(X['data']))
y = np.zeros(len(x))
fig, ax = plt.subplots(figsize=(10,5))
plt.plot(x, X['data'])
plt.plot(x, y)
plt.show()'''
