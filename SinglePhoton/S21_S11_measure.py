import pyvisa
import numpy as np

VNA_IP = "193.206.156.99"

rm = pyvisa.ResourceManager()
vna = rm.open_resource(f"TCPIP0::{VNA_IP}::inst0::INSTR")
vna.timeout = 30000  # 30 secondi per sweep lento
vna.read_termination = '\n'
vna.write_termination = '\n'

print("Connected to:", vna.query("*IDN?"))

# Preset e pulizia errori
vna.write("*CLS")
vna.write("SYST:PRES;*OPC?")
vna.read()

# Modalità Network Analyzer
vna.write("INST:SEL 'NA';*OPC?")
vna.read()

# Frequenze di Sweep
vna.write("SENS:FREQ:START 1e9")  # Frequenza di inizio: 1 GHz
vna.write("SENS:FREQ:STOP 2e9")   # Frequenza di fine: 2 GHz
vna.write("SENS:SWE:POIN 10")     # Numero di punti di sweep: 10

# Misura S11
vna.write("CALC:PAR:DEF 'S11',S11")  # Impostazione di S11
vna.write("CALC:PAR:SEL 'S11'")      # Selezione di S11
vna.write("CALC:FORM REAL,IMAG")    # Re + Im
vna.write("INIT:IMM")
vna.query("*OPC?")  # blocca finché sweep finito

# Leggi i dati S11: primi 10 punti
data_s11 = vna.query_ascii_values("CALC:DATA:SDAT?")
print("Raw S11 data returned:", data_s11)

# Stampa i risultati per i 10 punti di S11
for i in range(10):
    s11_point = complex(data_s11[2*i], data_s11[2*i+1])  # Ogni punto è composto da Re e Im
    amplitude = 20 * np.log10(abs(s11_point))    # Calcolo dell'ampiezza in dB
    phase = np.angle(s11_point, deg=True)       # Calcolo della fase in gradi
    print(f"S11 Punto {i+1}: {s11_point} | Amp: {amplitude:.2f} dB | Phase: {phase:.2f}°")

# Misura S21
vna.write("CALC:PAR:DEF 'S21',S21")  # Impostazione di S21
vna.write("CALC:PAR:SEL 'S21'")      # Selezione di S21
vna.write("CALC:FORM REAL,IMAG")     # Re + Im
vna.write("INIT:IMM")
vna.query("*OPC?")  # blocca finché sweep finito

# Leggi i dati S21: primi 10 punti
data_s21 = vna.query_ascii_values("CALC:DATA:SDAT?")
print("Raw S21 data returned:", data_s21)

# Stampa i risultati per i 10 punti di S21
for i in range(10):
    s21_point = complex(data_s21[2*i], data_s21[2*i+1])  # Ogni punto è composto da Re e Im
    amplitude = 20 * np.log10(abs(s21_point))    # Calcolo dell'ampiezza in dB
    phase = np.angle(s21_point, deg=True)       # Calcolo della fase in gradi
    print(f"S21 Punto {i+1}: {s21_point} | Amp: {amplitude:.2f} dB | Phase: {phase:.2f}°")

vna.close()
