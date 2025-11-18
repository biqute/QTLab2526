import pandas as pd
import matplotlib.pyplot as plt

# Percorso completo del file CSV
file_path = r"C:\Users\kid\labQT\Lab2025\3D Qubit\QTLab2526\SinglePhoton\Data_cavi_blu\S21_data_50medie_hunger"

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
