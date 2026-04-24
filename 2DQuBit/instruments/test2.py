import numpy as np
import pyvisa
import classes2
import matplotlib.pyplot as plt
import warnings
import time

dict_par = dict(A = 1, f = 3e7, mu = 0.0, sig = 1e-7,n_sigma = 3, name = 'singleshot', plot = False, N_cycles = 1)

'''my_lo = classes2.LO(name='COM9')
print(my_lo.get_IDN())
'''#classes2.acquire_singleshot(dict_par)

classes2.acquire_IQ(dict_par)







'''
tds = classes2.TDS('3')
pars_1 = tds.acquire_all()
print(pars_1)
trig_1 = tds.acquire_trig()
print(trig_1)


classes2.acquire_singleshot(dict_par)

pars_2 = tds.acquire_all()
trig_2 = tds.acquire_trig()


print(my_sdg.get_IDN())
my_sdg.turn_ON(ch=1)
my_sdg.set_arb_formwave(ch=1, wtp='sine', index=19)
#my_sdg.upload_waveform(dict_par)
my_sdg.set_freq(1, 3e6)
my_sdg.set_amp(1, 1)
time.sleep(1)
tds = classes2.TDS('3')
I, Q = tds.plot_acquisition(1)
phi = []
for i in range(len(Q['data'])):
        phi_point = np.arctan2(Q['data'][i],I['data'][i])
        phi.append(phi_point)
fig, ax = plt.subplots(figsize=(10,5))
X_phi = np.linspace(0, len(phi)/I['sample_rate'], len(phi))
z = np.ones(len(X_phi))*np.pi/2
z_2 = np.ones(len(X_phi))*-np.pi/2
plt.plot(X_phi, z_2, color='red', linestyle='--')
plt.plot(X_phi, z, color='red', linestyle='--')
plt.plot(X_phi, phi)
plt.plot()
plt.show()'''