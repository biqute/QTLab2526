#!/usr/bin/env python3
from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt


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

        # Salvo x originale, userò x/2 nel plot
        records.append((x_val, mean, std, path.name))

    if not records:
        print("Nessun file valido trovato (problema con i nomi file?).")
        return

    # Ordina per x (valore nel nome file)
    records.sort(key=lambda r: r[0])

    # Stampa riepilogo
    print("file,x_from_name,mean,std")
    for x, mean, std, fname in records:
        print(f"{fname},{x},{mean},{std}")

    # Prepara il plot
    xs = [(r[0] / 2.0)*1000 for r in records]   # <-- qui divido x per 2
    means = [r[1] for r in records]
    stds = [r[2] for r in records]

    # Solo punti con barre di errore (niente linea: fmt='o')
    plt.errorbar(xs, means, yerr=stds, fmt='o', capsize=4)
    plt.xlabel("V_DC (mV)")
    plt.ylabel("V_FD (V)")
    plt.title("V_FD vs V_DC")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
