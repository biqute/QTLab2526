import numpy as np
import matplotlib.pyplot as plt

data = np.load("spettroscopia_qubit.npz")
x = data['asse_x_vna']
y = data['asse_y_drive']
I = data['I_data']
Q = data['Q_data']
magnitude = np.abs(I + 1j*Q)  
X, Y = np.meshgrid(x, y)

plt.imshow(magnitude, extent=(x.min(), x.max(), y.min(), y.max()), aspect='auto', origin='lower')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Drive Frequency (Hz)')
plt.title('2-Tone Spectroscopy')
plt.colorbar(label='Magnitude')
plt.show()
