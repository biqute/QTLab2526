import pyvisa
import numpy as np
import matplotlib.pyplot as plt

# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

VNA_IP = "193.206.156.99"

rm = pyvisa.ResourceManager()
vna = rm.open_resource(f"TCPIP0::{VNA_IP}::inst0::INSTR")
vna.timeout =  20000
print("Connected to:", vna.query("*IDN?"))

vna.clear() #clear remote interface

vna.write ("*CLS")

# Check Error Queue
initial_error_check = str(vna.query('SYST:ERR?'))
print('Initial Error Check : {}\n'.format(initial_error_check))

vna.write("INST:SEL 'NA'", "Failed to select NA mode.") # Newtwork Analyzer
vna.write("SENS:AVER:MODE SWEEP") # Average mode set to sweep
vna.write("DISP:WIND:TRAC1:Y:AUTO") # Turn on autoscaling on the y axis

f_min = 4e9
f_max = 6e9
npoints= 5

vna.write(f"SENS:FREQ:START {f_min}") 
vna.write(f"SENS:FREQ:STOP {f_max}")
vna.write(f"SENS:SWE:POIN {npoints}")

# Misura S11
vna.write("CALC:PAR:DEF 'S11',S11")  # Impostazione di S11
vna.write("CALC:PAR:SEL 'S11'")      # Selezione di S11
vna.write("CALC:FORM REAL,IMAG")    # Re + Im
vna.write("INIT:IMM")
vna.query("*OPC?")  # blocca finché sweep finito

# Leggi i dati S11
raw_data_s11 = vna.query_ascii_values("CALC:DATA:SDAT?")
#print("Raw S11 data returned:", data_s11)

# Conversione in array complesso
data_s11 = np.array(raw_data_s11[::2]) + 1j*np.array(raw_data_s11[1::2])

npoints = len(data_s11)

y_values = np.array(npoints)
x_values = np.array(npoints)

# Creazione dell'array di valori Y (dB)
y_values = 20 * np.log10(np.abs(data_s11))

# Creazione dell'array X (per esempio, valori di frequenza, se disponibili)
x_values = np.linspace(f_min, f_max, npoints)

data_to_save = np.column_stack((x_values, y_values))

# Salvataggio in un file di testo
np.savetxt('dati_s11.txt', data_to_save, header='Frequenza (Hz)\tS11 (dB)', fmt='%.6e', delimiter='\t')

fig, ax = plt.subplots()
ax.set_xlabel(r"$f$(GHz)")
ax.set_ylabel(r"$S11$ Power in dB)")
ax.plot(x_values,y_values)
plt.show()  
    



