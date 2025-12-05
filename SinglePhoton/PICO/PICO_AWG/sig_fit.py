#!/usr/bin/env python3
from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit


def parse_x_from_filename(path: Path) -> float:
    """
    Estrae il valore numerico dal nome file.
    Esempi:
      '-1.400V.csv'        -> -1.4
      '1.395V.csv'         -> 1.395
      'bias_-1.400V.csv'   -> -1.4
    """
    stem = path.stem  # nome senza .csv
    m = re.search(r'([-+]?\d+\.?\d*)\s*[Vv]?', stem)
    if not m:
        raise ValueError(f"Impossibile estrarre il valore da filename: {path.name}")
    return float(m.group(1))


def sigmoid(x, A, B, x0, k):
    """Sigmoide/logistica a 4 parametri."""
    return A + (B - A) / (1.0 + np.exp(-(x - x0) / k))


def main():
    csv_files = sorted(Path(".").glob("*.csv"))
    if not csv_files:
        print("Nessun file .csv trovato nella cartella corrente.")
        return

    records = []

    for path in csv_files:
        # Salta la seconda riga con le unità "(ms),(V)"
        df = pd.read_csv(path, skiprows=[1])

        # Seconda colonna (Channel A)
        col = df.iloc[:, 1]
        y = pd.to_numeric(col, errors="coerce").dropna()

        mean = y.mean()
        std = y.std(ddof=1)

        try:
            x_val = parse_x_from_filename(path)
        except ValueError as e:
            print(f"# WARNING: {e}")
            continue

        records.append((x_val / 2.0, mean, std, path.name))  # x/2 qui

    if not records:
        print("Nessun file valido trovato.")
        return

    # Ordina per x
    records.sort(key=lambda r: r[0])

    xs = np.array([r[0] for r in records], dtype=float)
    ys = np.array([r[1] for r in records], dtype=float)
    stds = np.array([r[2] for r in records], dtype=float)

    # Stampa riepilogo numerico
    print("file,x_half,mean,std")
    for x, mean, std, fname in records:
        print(f"{fname},{x},{mean},{std}")

    # ----- Fit sigmoide -----
    # Stime iniziali ragionevoli
    A0 = float(ys.min())
    B0 = float(ys.max())
    x0_0 = float(xs.mean())
    k0 = (xs.max() - xs.min()) / 4.0 if xs.max() > xs.min() else 1.0

    # Evita sigma=0
    sigma = stds.copy()
    sigma[sigma == 0] = sigma[sigma > 0].min() if (sigma > 0).any() else 1.0

    try:
        popt, pcov = curve_fit(
            sigmoid,
            xs,
            ys,
            p0=[A0, B0, x0_0, k0],
            sigma=sigma,
            absolute_sigma=True,
            maxfev=10000,
        )
        print("\nParametri fit sigmoide (A, B, x0, k):")
        print(popt)
        fit_ok = True
    except Exception as e:
        print(f"\nFit sigmoide fallito: {e}")
        fit_ok = False

    # ----- Plot -----
    plt.figure()

    # Punti sperimentali con barre di errore (niente linea di collegamento)
    plt.errorbar(xs, ys, yerr=stds, fmt='o', capsize=4, label="dati")

    # Curva fittata
    if fit_ok:
        x_fit = np.linspace(xs.min(), xs.max(), 400)
        y_fit = sigmoid(x_fit, *popt)
        plt.plot(x_fit, y_fit, label="fit sigmoide")

    plt.xlabel("Valore da filename / 2 (V)")
    plt.ylabel("Media Channel A (V)")
    plt.title("Mean ± std di Channel A con fit sigmoide")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
