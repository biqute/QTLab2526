from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
import numpy as np
import matplotlib.pyplot as plt

file_name = "../qubit0/Data/ZOOMpower_-40"

data = np.loadtxt(file_name+".txt")
frequencies = data[:, 0]
real_S21 = data[:, 1]     # Parte reale di S21
imag_S21 = data[:, 2]     # Parte immaginaria di S21

real_S21_filtered = savgol_filter(real_S21, 1000, 4)  # Filtro Savitzky-Golay
imag_S21_filtered = savgol_filter(imag_S21, 1000, 4)  # Filtro Savitzky-Golay

signal = np.abs(real_S21_filtered + 1j * imag_S21_filtered)
phase = np.unwrap(np.angle(real_S21_filtered + 1j * imag_S21_filtered))

file_name = file_name + "_filtered.txt"
np.savetxt(file_name, np.column_stack((frequencies, real_S21_filtered, phase)), delimiter='\t', header='Frequency(Hz)\tSignal\tPhase(rad)', comments='')