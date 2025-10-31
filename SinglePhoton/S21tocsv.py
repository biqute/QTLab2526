import pyvisa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# ==============================
# Configurazione iniziale
# ==============================
VNA_IP = "193.206.156.99"

rm = pyvisa.ResourceManager()
vna = rm.open_resource(f"TCPIP0::{VNA_IP}::inst0::INSTR")
vna.timeout = 30000  # 30 secondi
vna.read_termination = '\n'
vna.write_termination = '\n'

print("Connected to:", vna.query("*IDN?"))

# ==============================
# Preset e setup
# ==============================
vna.write("*CLS")
vna.query("SYST:PRES;*OPC?")
vna.query("INST:SEL 'NA';*OPC?")

# Impostazione sweep
f_min = 1e9
f_max = 2e9
vna.write(f"SENS:FREQ:START {f_min}")
vna.write(f"SENS:FREQ:STOP {f_max}")
vna.write("SENS:SWE:POIN 100")

# ==============================
# Misura S21
# ==============================
vna.write("CALC:PAR:DEF 'S21',S21")
vna.write("CALC:PAR:SEL 'S21'")
vna.write("INIT:IMM")
vna.query("*OPC?")

# Lettura dati Re + Im
data_s21 = vna.query_ascii_values("CALC:DATA:SDAT?")
num_points = len(data_s21) // 2

# ==============================
# Elaborazione dati
# ==============================
freqs = np.linspace(f_min, f_max, num_points)
re_values = [data_s21[2*i] for i in range(num_points)]
im_values = [data_s21[2*i+1] for i in range(num_points)]

# Stampa risultati
for i in range(num_points):
    s21_point = complex(re_values[i], im_values[i])
    amplitude = 20 * np.log10(abs(s21_point))
    phase = np.angle(s21_point, deg=True)
    print(f"S21 Punto {i+1}: {s21_point} | Amp: {amplitude:.2f} dB | Phase: {phase:.2f}°")

# ==============================
# Salvataggio su CSV nella cartella SinglePhoton
# ==============================
cartella_destinazione = os.path.join(os.path.dirname(__file__), "Data")
os.makedirs(cartella_destinazione, exist_ok=True)  # Crea la cartella se non esiste
file_csv = os.path.join(cartella_destinazione, "S21_data.csv")

df = pd.DataFrame({
    "Frequenza (Hz)": freqs,
    "Re(S21)": re_values,
    "Im(S21)": im_values
})
df.to_csv(file_csv, index=False, float_format="%.3f")
print(f"✅ Dati S21 salvati in '{file_csv}'")

# ==============================
# Chiusura connessione
# ==============================
vna.close()
print("Connessione chiusa.")
