import numpy as np
import matplotlib.pyplot as plt
import pyvisa 
import  binascii
import struct
import string


# Parametri del segnale
f_c = 50         # Frequenza portante 
sample_rate = 5e3
duration = 0.1  # Durata totale del segnale 
A = 1.0             # Ampiezza massima

# Array del tempo e punti totali
t = np.linspace(-duration/2 ,duration/2,50000)
N = len(t)


# 1. Creare la Gaussiana (Inviluppo)
mu = duration/2   # Centro dell'impulso
sigma = 5e-3       # Deviazione standard (largheza dell'impulso)
gaussian_envelope = np.exp(-0.5 * ((t - mu) / sigma)**2)

# 2. Creare l'Onda Sinusoidale (Portante)
sine_wave = np.sin(2 * np.pi * f_c * t)
plt.figure()
plt.plot(t, sine_wave)
plt.show()
# 3. Modulazione: Inviluppo * Portante
modulated_sine = A * gaussian_envelope * sine_wave

# 4. Normalizzazione e Conversione (per l'SDG)
# Molti SDG richiedono dati interi a 14 o 16 bit (es. da -8191 a +8191 per 14 bit)
max_val = 2**15-1 # Valore massimo per un SDG a 16 bit
arb_data = (sine_wave*max_val).astype(np.int16)
data_b = [f'{hex(arb_data[i])[-4:]}'for i in range(len(arb_data))]
data_b= [s.replace("x", "") for s in data_b]

data_b_s = ', '.join(data_b)


print(arb_data[200:400])
print(data_b_s)


rm = pyvisa.ResourceManager ()
_SDG = rm.open_resource("TCPIP0::193.206.156.10::inst0::INSTR")
a =_SDG.query("*IDN?") 
print(a)
ch = 1
### My try

_SDG.write("C1:WVDT WVNM,wave2,FREQ,20000.0,AMPL,5.0,OFST,0.0,PHASE,0.0,WAVEDATA,%s" % (data_b))
_SDG.write("C1:ARWV NAME,wave2")


#### Gemini try
'''
# Imposta Sample Rate e Nome
_SDG.write(f"C{ch}:ARWV SRAT,{sample_rate}")
_SDG.write(f"C{ch}:ARWV NAME,GAUSSIAN_MOD")

# 2.1 Comando SCPI per la scrittura (SOLO l'intestazione)
command_header = f"C{ch}:ARWV DATA,VOLATILE," 

# 2.2 Invio tramite write_binary_values di PyVISA
try:
    _SDG.write_binary_values(
        command_header,     # Stringa del comando SCPI (escl. blocco binario #...)
        arb_data,           # L'array NumPy da inviare
        datatype='h',       # 'h' = short integer (16 bit), corretto per SDG6052X
        is_big_endian=False, # Formato Little Endian (comune negli SDG)
    )
    # 2.3 Attendere la conclusione del caricamento
    a= _SDG.query(f"*OPC?") 
    print("Caricamento completato con successo.", a)
    _SDG.write(f"C{ch}:ARWV SAVE,NAME,GAUSSIAN_MOD")
    _SDG.query(f"*OPC?")
    print("   -> Salvataggio completato.")
    _SDG.write(f"C{ch}:ARWV LOAD,NAME,GAUSSIAN_MOD")
    _SDG.query(f"*OPC?")

except Exception as e:
    print(f"Errore durante l'invio dei dati binari: {e}")
    # Considera di usare: _SDG.write(f"C{ch}:ARWV NAME,USER") per uscire da uno stato ARB bloccato
    exit()


_SDG.write(f"C{ch}:WVTP ARB")
_SDG.write(f"C{ch}:ARWV NAME,GAUSSIAN_MOD")
arb_current_name = _SDG.query(f"C{ch}:ARWV?") 
print(f"Nome ARB selezionato: {arb_current_name}")

# 1. Verifica il tipo di forma d'onda (dovrebbe essere ARB)
waveform_type = _SDG.query(f"C{ch}:BSWV?")
print(f"Tipo di onda selezionato: {waveform_type}")

# 2. Verifica il nome ARB attualmente puntato (dovrebbe essere GAUSSIAN_MOD)'''
