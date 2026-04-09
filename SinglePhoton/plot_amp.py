import pandas as pd
import matplotlib.pyplot as plt

# Percorso completo del file CSV
file_path = r"C:\Users\kid\labQT\Lab2025\Single photon\QTLab2526\SinglePhoton\VNA\CRIO_measures_new\11_95mk\picco1_big_new.csv"

# Leggi il CSV
df = pd.read_csv(file_path)

# Grafico ampiezza vs frequenza
plt.figure(figsize=(8,5))
plt.plot(df['Frequenze (Hz)'], df['Ampiezza'], marker='o', linestyle='-')
plt.xlabel("Frequenza (Hz)")
plt.ylabel("Ampiezza")
plt.title("Ampiezza vs Frequenza")
plt.grid(True)
plt.tight_layout()
plt.show()
