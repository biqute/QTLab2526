import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.append("../classes")
from PSA import PSA
from data import Data

SETTINGS = {
    "points": 400,
    "min_freq": 4.6e9, # Hz
    "max_freq": 5.6e9, # Hz
    "timeout": 10e3, # ms
}

ip = '193.206.156.99'

myPSA = PSA(ip)

myPSA.set_timeout(SETTINGS["timeout"])
myPSA.set_min_freq(SETTINGS["min_freq"])
myPSA.set_max_freq(SETTINGS["max_freq"])
myPSA.set_point_count(SETTINGS["points"])

datay = myPSA.read_data()
datax = np.linspace(SETTINGS["min_freq"],SETTINGS["max_freq"],SETTINGS["points"])

d = Data(datax, datay)


d.fast_plot(datax, datay, 
                Title="PSA data", 
                x_title="frequencies", 
                y_title="Spectrum")

#plt.plot(datax, datay)
#plt.title("Random Plot")
#plt.xlabel("Frequency (Hz)")
#plt.ylabel("dB")
#plt.grid()
#plt.show()



# SMA100B
#rm_1 = pyvisa.ResourceManager()
#resource_1 = rm_1.open_resource('tcpip0::192.168.40.15::inst0::INSTR')
#print(resource_1.query("*IDN?"))
