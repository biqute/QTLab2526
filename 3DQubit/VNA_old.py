import pyvisa
import numpy as np
import matplotlib.pyplot as plt

# This makes your plot look like latex. Great for writing papers!
'''plt.rcParams.update({
    "text.usetex": False, #controlla forse serve True
    "font.family": "Helvetica"
})'''

VNA_IP = "193.206.156.99"

rm = pyvisa.ResourceManager()
vna = rm.open_resource(f"TCPIP0::{VNA_IP}::inst0::INSTR")
vna.timeout =  2000
print("Connected to:", vna.query("*IDN?"))
print(vna.query("SYST:ERR?"))


# --- Reset e pulizia ---
vna.write("*CLS")     # clear status
vna.clear()           # clear comm buffer
print(vna.query("SYST:ERR?"))


# Check Error Queue
initial_error_check = str(vna.query('SYST:ERR?'))
print('Initial Error Check : {}\n'.format(initial_error_check))
print(" 1", vna.query("SYST:ERR?"))


vna.write("INST:SEL 'NA'")
vna.write("SENS:AVER:MODE SWEEP") # Average mode set to sweep
vna.write("DISP:WIND:TRAC1:Y:AUTO") # Turn on autoscaling on the y axis
print("2", vna.query("SYST:ERR?"))

f_min = 4e9
f_max = 4.12e9
npoints = 401

vna.write(f"SENS:FREQ:START {f_min}") 
vna.write(f"SENS:FREQ:STOP {f_max}")
vna.write(f"SENS:SWE:POIN {npoints}")
print("3", vna.query("SYST:ERR?"))

# Misura S21
vna.write('CALC:PAR:DEF S21measure,S21')  # traccia senza apici singoli
print("Errore dopo definizione traccia:", vna.query("SYST:ERR?"))

vna.write('CALC:PAR:SEL S21measure')
print("Errore dopo selezione traccia:", vna.query("SYST:ERR?"))

vna.write("INIT:IMM")
print("6", vna.query("SYST:ERR?"))

vna.query("*OPC?")  # blocca finché sweep finito
print("7", vna.query("SYST:ERR?"))


# Leggi i dati S21
raw_data_s21 = vna.query_ascii_values("CALC:DATA:SDAT?")
#print("Raw S21 data returned:", data_s21)

# Conversione in array complesso
data_s21 = np.array(raw_data_s21[::2]) + 1j*np.array(raw_data_s21[1::2])

npoints = len(data_s21)

amp_S21 = np.array(npoints)
frequencies = np.array(npoints)

# Creazione dell'array di valori Y (dB)
amp_S21 = 20 * np.log10(np.abs(data_s21))

# Creazione dell'array X (per esempio, valori di frequenza, se disponibili)
frequencies = np.linspace(f_min, f_max, npoints)

data_to_save = np.column_stack((frequencies, amp_S21))

# Salvataggio in un file di testo
np.savetxt('dati_s21.txt', data_to_save, header='Frequenza (Hz)\tS21 (dB)', fmt='%.6e', delimiter='\t')

fig, ax_1 = plt.subplots()
ax_1.set_xlabel(r"$f$(GHz)")
ax_1.set_ylabel(r"($S21$ Power in dB)")
ax_1.plot(frequencies,amp_S21)
plt.show()  