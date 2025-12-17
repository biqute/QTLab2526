import numpy as np
import matplotlib.pyplot as plt
import pyvisa 
import warnings

#=====================GAUSSIAN_IMPULSE========================
def gaussian_sine(x, A=1.0, f=3, mu=0.0, sigma=0.5):
    
    gauss = A * np.exp(-((x - mu)**2) / (2 * sigma**2))
    sine = np.sin(2 * np.pi * f * x)
    
    y = gauss * sine
    return y
#=====================DATA_GENERATION==========================
def upload_waveform(name, func, interval, samples_per_second):
    duration = interval[1] - interval[0]
    samples = int(duration * samples_per_second)
    array = np.zeros(samples, dtype=np.int16)
    N = 15
    cropped = 0
    for i in range(0,samples):
        f = func(interval[0] + i / samples_per_second)
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

    SDG.write_binary_values(f"C1:WVDT WVNM,{name},LENGTH,{samples},WAVEDATA,", array, datatype="h")
    SDG.write(f"C1:ARWV NAME,{name}")
    
    arb_freq = 1/duration
    print("FREQ = ", arb_freq)
    print("duration = ", duration)
    print("samples", samples)

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
    SDG.write("C1:BTWV MTRIG")

    print(SDG.query("*OPC?"))



sigma_ = 0.5
interval = [-5*sigma_, +5*sigma_]
upload_waveform('singleshot', gaussian_sine, interval, 100)