import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# 1. LETTURA CORRETTA
# =========================================================
file_csv = "quality_factors.csv"

df = pd.read_csv(file_csv, sep=r"\s+", engine="python")

# pulizia nomi colonne
df.columns = df.columns.str.strip()

print("Colonne trovate:", df.columns.tolist())
print(df.head())

# =========================================================
# 2. CONVERSIONE
# =========================================================
for c in df.columns:
    df[c] = pd.to_numeric(df[c], errors='coerce')

# rimuove righe rotte
df = df.dropna()

print(f"Punti validi: {len(df)}")

# =========================================================
# 3. DATI
# =========================================================
T = df["T(mK)"].values

Q_cols = ["R1","R3","R5"]

# =========================================================
# 4. PLOT 1/Q
# =========================================================
plt.figure(figsize=(8,6))

colors = ["tab:blue", "tab:red"]

for i, qcol in enumerate(Q_cols):

    if qcol not in df.columns:
        continue

    Q = df[qcol].values

    mask = Q > 0

    plt.plot(
        T[mask],
        1.0 / Q[mask],
        'o-',
        label=qcol,
        #color=colors[i]
    )

plt.xlabel("T (mK)")
plt.ylabel("1/Q")
plt.title("Inverse Quality Factor vs Temperature")
plt.grid(True, alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()