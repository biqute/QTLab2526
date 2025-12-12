#!/usr/bin/env python3
from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import odr

def parse_x_from_filename(path: Path) -> float:
    """
    Estrae il valore numerico dal nome file.
    """
    stem = path.stem
    m = re.search(r'([-+]?\d+\.?\d*)\s*[Vv]?', stem)
    if not m:
        raise ValueError(f"Impossibile estrarre il valore da filename: {path.name}")
    return float(m.group(1))

def sigmoid_model(p, x):
    """
    Modello Sigmoide per ODR: f(beta, x)
    p = [A, B, x0, k]
    """
    A, B, x0, k = p
    return A + (B - A) / (1.0 + np.exp(-(x - x0) / k))

def main():
    csv_files = sorted(Path(".").glob("*.csv"))
    if not csv_files:
        print("Nessun file .csv trovato nella cartella corrente.")
        return

    records = []

    for path in csv_files:
        df = pd.read_csv(path, skiprows=[1])
        col = df.iloc[:, 1]
        y = pd.to_numeric(col, errors="coerce").dropna()

        mean = y.mean()
        std = y.std(ddof=1)

        try:
            x_val = parse_x_from_filename(path)
        except ValueError as e:
            print(f"# WARNING: {e}")
            continue

        records.append((x_val / 2.0, mean, std, path.name))

    if not records:
        print("Nessun file valido trovato.")
        return

    # Ordina i dati
    records.sort(key=lambda r: r[0])

    xs = np.array([r[0] for r in records], dtype=float)
    ys = np.array([r[1] for r in records], dtype=float)
    y_err = np.array([r[2] for r in records], dtype=float)

    # Errore su X fisso a 1 mV (0.001 V)
    x_err_val = 1e-3
    x_err = np.full_like(xs, x_err_val)

    # Evita pesi infiniti se l'errore è 0
    if np.any(y_err == 0):
        min_pos_err = y_err[y_err > 0].min() if (y_err > 0).any() else 1.0
        y_err[y_err == 0] = min_pos_err

    print("file,x_half,mean,std_y")
    for x, mean, std, fname in records:
        print(f"{fname},{x},{mean},{std}")

    # ----- Fit ODR -----
    A0 = float(ys.min())
    B0 = float(ys.max())
    x0_0 = float(xs.mean())
    k0 = (xs.max() - xs.min()) / 4.0 if xs.max() > xs.min() else 1.0
    beta0 = [A0, B0, x0_0, k0]

    try:
        model = odr.Model(sigmoid_model)
        # sx e sy sono le deviazioni standard (1/sigma^2 sono i pesi)
        data = odr.RealData(xs, ys, sx=x_err, sy=y_err)
        my_odr = odr.ODR(data, model, beta0=beta0)
        
        output = my_odr.run()
        
        popt = output.beta
        perr = np.sqrt(np.diag(output.cov_beta)) # Errori parametri
        
        # --- Calcolo Chi Quadro ---
        chisq = output.sum_square  # Somma pesata dei quadrati dei residui
        dof = len(xs) - len(beta0) # Gradi di libertà: N_punti - N_parametri
        chisq_red = chisq / dof    # Chi quadro ridotto

        print("-" * 40)
        print("RISULTATI FIT ODR")
        print(f"Chi Quadro:         {chisq:.4f}")
        print(f"Gradi di libertà:   {dof}")
        print(f"Chi Quadro Ridotto: {chisq_red:.4f}")
        print("-" * 40)
        print("Parametri (A, B, x0, k):")
        print(popt)
        print("Errori parametri:")
        print(perr)
        
        fit_ok = True
    except Exception as e:
        print(f"\nFit ODR fallito: {e}")
        fit_ok = False
        popt = None

    # ----- Plot -----
    plt.figure(figsize=(8, 6))

    plt.errorbar(xs, ys, xerr=x_err_val, yerr=y_err, fmt='o', capsize=4, label="Dati sperimentali")

    if fit_ok:
        x_fit = np.linspace(xs.min(), xs.max(), 400)
        y_fit = sigmoid_model(popt, x_fit)
        
        # Aggiungo info chi quadro in legenda
        label_fit = f"Fit Sigmoide\n$\chi^2_\\nu$ = {chisq_red:.2f}"
        plt.plot(x_fit, y_fit, 'r-', label=label_fit)

    plt.xlabel("V_DC (V)")
    plt.ylabel("V_FD (V)")
    plt.title("Fit Sigmoide con Errori XY (ODR)")
    plt.grid(True, alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()