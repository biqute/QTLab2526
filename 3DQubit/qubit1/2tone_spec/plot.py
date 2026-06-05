import numpy as np
import matplotlib.pyplot as plt

data = np.load("0span_data.npz")
#data = np.load("PowerSweep_data.npz")
x = data['asse_x_vna']
I = data['I_data']
Q = data['Q_data']
drive = True
try:
    y = data['asse_y_drive']
except:
    y = data['asse_y_pow']
    drive = False
magnitude = np.abs(I + 1j*Q)  
X, Y = np.meshgrid(x, y)

plt.imshow(magnitude, extent=(x.min(), x.max(), y.min(), y.max()), aspect='auto', origin='lower')
plt.xlabel('Frequency (Hz)')
if drive:
    plt.ylabel('Drive Frequency (Hz)')
else:
    plt.ylabel('Drive Power (dBm)')
plt.title('2-Tone Spectroscopy')
plt.colorbar(label='Magnitude')
plt.show()
