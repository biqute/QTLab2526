import numpy as np
import matplotlib.pyplot as plt
import pyvisa 
import warnings
from classes import TDS


#=====================GAUSSIAN_IMPULSE========================
def gaussian_sine(x, sigma=1e-7, f=5e7, A=1.0, mu=0.0):
    
    gauss = A * np.exp(-((x - mu)**2) / (2 * sigma**2))
    sine = np.sin(2 * np.pi * f * x)
    y = gauss * sine
    return y
#=====================DATA_GENERATION==========================
def upload_waveform(name, func, sig, freq):
    n_sigma = 3
    interval = [-n_sigma*sig, +n_sigma*sig]
    duration = interval[1] - interval[0]
    samples_per_second = 2.4e9
    if duration * samples_per_second > 2400:
        samples_per_second = 2400 / duration
    
    samples = int(duration * samples_per_second)
    array = np.zeros(samples, dtype=np.int16)
    N = 15
    cropped = 0
    for i in range(0,samples):
        f = func(interval[0] + i / samples_per_second, sigma=sig, f=freq)
        n = int(round((2**N)*f))

        if n > (2**N - 1): 
            n = 2**N - 1
            cropped += 1
        if n < -2**N: 
            n = -2**N
            cropped += 1
        array[i] = n
        
        if cropped > 0: 
            warnings.warn(f"The function 'func' was cropped to the range [-1, +1], for a total of {cropped} cropped samples.", stacklevel=2)
    
    plt.figure(figsize=(10, 5))
    plt.plot(np.linspace(interval[0], interval[1], samples), array)
    plt.show() 

    array[0] = 0
    array[-1] = 0
    print(array)
    #=========================UPLOAD_DATA_WAVEFORM====================================
    rm = pyvisa.ResourceManager ()
    SDG = rm.open_resource("TCPIP0::193.206.156.10::inst0::INSTR")

    SDG.write_binary_values(f"C1:WVDT WVNM,{name},LENGTH,{samples},WAVEDATA,", array, datatype="h", is_big_endian=False, header_fmt='empty')
    SDG.write(f"C1:ARWV NAME,{name}")
    
    arb_freq = 1/duration
    print("duration = ", duration)
    print("samples", samples)
    print("frequenza del segnale gaussiano = ", arb_freq)

    SDG.write(f"C1:BSWV FRQ,{arb_freq}")

    # ========================== BURST ==============================================
    SDG.write("C1:BTWV MODE,NCYC") 
    SDG.write("C1:BTWV NCYC,1") 
    SDG.write(f"C1:BTWV TIME,1")
    SDG.write(f"C1:BTWV PRD,3")
    SDG.write("C1:BTWV TRSR,MAN")
    SDG.write("C1:BTWV STATE,ON")
    SDG.write("C1:OUTP ON") 
    SDG.write("C1:BTWV ILVL,0V")
    #SDG.write("C1:BTWV MTRIG")

    print(SDG.query("*OPC?"))



sigma_gaus = 1e-7
frequenza_sin = 1e7
tds = TDS('3')
tds.set_hor_scale(sigma_gaus * 0.5)
upload_waveform('singleshot', gaussian_sine, sigma_gaus, frequenza_sin)
tds.set_acquire_state('ON')