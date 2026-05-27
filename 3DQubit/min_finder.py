import sys
sys.path.append("../classes")
import matplotlib.pyplot as plt
import numpy as np

filename = "qubit0/Data/ZOOMpower_-39.txt"
data = np.loadtxt(filename)

freq = data[:, 0]/1e9  # Frequenze in GHz
I = data[:, 1]   
Q = data[:, 2]     
signal = 20*np.log10(np.sqrt(I**2 + Q**2))

min_index = np.argmin(signal)
min_freq = freq[min_index]

print(f"Minimum signal for {filename} at frequency: {min_freq:.5f} GHz")


