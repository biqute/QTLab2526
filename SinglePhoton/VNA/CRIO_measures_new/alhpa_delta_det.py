import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# =========================================================
# 1. LETTURA CSV (robusta)
# =========================================================
file_csv = "fr_vs_temp.csv"

df = pd.read_csv(file_csv, sep=r'\s+|,', engine='python')  # accetta sia spazio che virgola

print("Colonne:", df.columns.tolist())

T_col = "T"
Terr_col = "Terr"
f_col = "P5"

# forza numerico (IMPORTANTISSIMO)
for c in [T_col, Terr_col, f_col]:
    df[c] = pd.to_numeric(df[c], errors='coerce')

df = df.dropna(subset=[T_col, Terr_col, f_col])
df = df.sort_values(by=T_col)

T = df[T_col].values
Terr = df[Terr_col].values
f = df[f_col].values

print(f"Punti finali usati nel fit: {len(T)}")

# =========================================================
# 2. MODELLO
# =========================================================
def f_vs_T(T_mK, f0, alpha, Delta_k, c):
    T_K = np.maximum(T_mK / 1000.0, 1e-6)

    mb_term = (alpha / 2.0) * np.sqrt((np.pi * Delta_k) / (2.0 * T_K)) \
              * np.exp(-Delta_k / T_K)

    return f0 * (1.0 - mb_term) + c

kB_eV = 8.617333262e-5

# =========================================================
# 3. FIT
# =========================================================
f0_guess = np.max(f)
guess = [f0_guess, 0.05, 2.0, 0.0]  # f0, alpha, Delta, c

bounds = (
    [f0_guess * 0.98, 1e-6, 0.1, -0.000001],
    [f0_guess * 1.02, 1.0, 10.0, 0.000001]
)

print("Fit in corso...")

popt, pcov = curve_fit(
    f_vs_T,
    T,
    f,
    sigma=Terr,          # 🔥 ora usa errori reali
    absolute_sigma=True,
    p0=guess,
    bounds=bounds,
    maxfev=100000
)

f0, alpha, Delta_k, c = popt
perr = np.sqrt(np.diag(pcov))

f0_err, alpha_err, Delta_k_err, c_err = perr

Delta_ueV = Delta_k * kB_eV * 1e6
Delta_ueV_err = Delta_k_err * kB_eV * 1e6

# =========================================================
# 4. OUTPUT
# =========================================================
print("\n===== RISULTATI FIT =====")
print(f"f0     = {f0:.0f} ± {f0_err:.0f} Hz")
print(f"alpha  = {alpha:.4e} ± {alpha_err:.4e}")
print(f"Delta  = {Delta_k:.3f} ± {Delta_k_err:.3f} K")
print(f"c      = {c:.3f} ± {c_err:.3f}")
print(f"Delta  = {Delta_ueV:.2f} ± {Delta_ueV_err:.2f} µeV")

# =========================================================
# 5. PLOT (CORRETTO)
# =========================================================
plt.figure(figsize=(9,6))

# tutti i punti + barre errore T
plt.errorbar(
    T, f,
    xerr=Terr,
    fmt='o',
    color='black',
    ecolor='gray',
    capsize=3,
    label="dati sperimentali"
)

T_smooth = np.linspace(T.min(), T.max(), 400)

plt.plot(
    T_smooth,
    f_vs_T(T_smooth, *popt),
    'r-',
    lw=2,
    label="fit Mattis-Bardeen + c"
)

plt.xlabel("T (mK)")
plt.ylabel("frequenza")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()