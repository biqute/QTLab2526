import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import sys

# ── Modello fisico ─────────────────────────────────────────────
def model(Lk, A, Lg):
    return A / np.sqrt(Lk + Lg)

# ── Main ──────────────────────────────────────────────────────
def main():
    # File CSV da CLI o default
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "Lk_old/Lk_tot.csv"
    print(f"\nLoading: {csv_file}")

    # ── Lettura robusta CSV ────────────────────────────────────
    df = pd.read_csv(csv_file)
    
    # Pulisci nomi colonne (rimuove spazi e uniforma lowercase)
    df.columns = df.columns.str.strip().str.lower()

    print("Columns found:", df.columns.tolist())

    # Controllo colonne
    if "lk" not in df.columns:
        raise KeyError(f"Column 'Lk' not found. Available: {df.columns}")
    if "fr" not in df.columns:
        raise KeyError(f"Column 'fr' not found. Available: {df.columns}")

    # Estrai dati
    Lk = df["lk"].to_numpy(dtype=float)
    fr = df["fr"].to_numpy(dtype=float)

    # ── Fit ────────────────────────────────────────────────────
    p0 = [20, 1]  # guess iniziale [A, Lg]

    popt, pcov = curve_fit(model, Lk, fr, p0=p0, maxfev=10000)

    A_fit, Lg_fit = popt
    perr = np.sqrt(np.diag(pcov))

    print("\nFit results:")
    print(f"A  = {A_fit:.6f} ± {perr[0]:.6f}")
    print(f"Lg = {Lg_fit:.6f} ± {perr[1]:.6f}")

    # ── Curve fit ──────────────────────────────────────────────
    Lk_fit = np.linspace(min(Lk), max(Lk), 500)
    fr_fit = model(Lk_fit, *popt)

    # ── Plot ───────────────────────────────────────────────────
    plt.figure(figsize=(7,5))

    plt.plot(Lk, fr, 'o', label="Data", color="steelblue")
    plt.plot(Lk_fit, fr_fit, '-', color="crimson",
             label=f"Fit: A={A_fit:.2f}, Lg={Lg_fit:.2f}")

    plt.xlabel("Lk")
    plt.ylabel("Resonance frequency (GHz)")
    plt.title("f_res vs Lk")
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.show()

# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    main()