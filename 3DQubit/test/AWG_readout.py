import numpy as np
import sys; sys.path.append("../classes")
from AWG import AWG
import matplotlib.pyplot as plt


def gaussian(mu, sigma):
    norm = 2.0*sigma**2
    return lambda x: np.exp(-(x - mu)**2/norm)

T = 1e-6
sigma = 1e-7

# SDG6052X
myAWG = AWG(ip_address="193.206.156.10") # Check IP: Utility > Interface > LAN Setup > IP Address
myAWG.timeout = 10e3
myAWG.set_waveform(1, "Gauss")

myAWG.set_freq = 2000 # Hz
myAWG.set_amp = 2 # Vpp
