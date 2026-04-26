"""
MKID Internal Quality Factor Fitting Script
============================================
Fits 1/Q_i vs temperature data using the Mattis-Bardeen conductivity model
(Nambu approximation, valid for hf << 2*Delta and kBT << Delta):

    sigma1/sigma_n ≈ (4*Delta / hbar*omega) * exp(-Delta0/kBT) * sinh(xi) * K0(xi)
    sigma2/sigma_n ≈ (pi*Delta  / hbar*omega) * [1 - 2*exp(-Delta0/kBT) * exp(-xi) * I0(xi)]

    where xi = hbar*omega / (2*kB*T)

Two fit models are tested:

  Model 1 – Without Kondo correction (eq. 6 of Campana et al. 2024):
      1/Q_i = 1/Q_i(0) + alpha * sigma1 / (2*sigma2)

  Model 2 – With Kondo correction (eq. 8 of Campana et al. 2024):
      1/Q_i = 1/Q_i(0) + alpha * sigma1 / (2*sigma2) - b * ln(T / T_K)

Input CSV columns (header required, order flexible):
  f   – resonant frequency  [Hz]   (if values look like GHz, auto-scaled)
  T   – temperature          [K]    (if values look like mK,  auto-scaled)
  Qi  – internal quality factor  (dimensionless)

Usage:
  python fit_mkid_qi.py               # uses default filename below
  python fit_mkid_qi.py data.csv      # pass filename as first CLI argument
"""

import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import kv, iv
from pathlib import Path

# ── Physical constants ────────────────────────────────────────────────────────
k_B  = 1.380649e-23   # J / K
hbar = 1.054571817e-34 # J·s
eV   = 1.602176634e-19 # J / eV
meV  = eV * 1e-3       # J / meV

# ── Configuration – edit these if needed ─────────────────────────────────────
DEFAULT_CSV  = "p5.csv"          # fallback filename
CSV_SEP      = ","                 # column separator
# Column name aliases (case-insensitive).  First match wins.
COL_F_NAMES  = ["f", "freq", "frequency", "f0", "f_res"]
COL_T_NAMES  = ["t", "temp", "temperature"]
COL_QI_NAMES = ["qi", "q_i", "qint", "q_int"]

# Initial guess ranges for the fit parameters
alfa_sim       = 0.1    # simulated kinetic inductance fraction (0 < α < 1)
alfa_min = alfa_sim * 0.10 # lower bound
alfa_max = alfa_sim * 5 # upper bound
# Δ is expressed in meV throughout the fitting to keep numbers ~O(1).
DELTA_INIT_MEV = 0.15   # initial guess for energy gap  [meV]
ALPHA_INIT     = alfa_sim    # kinetic inductance fraction (0 < α < 1)
QI0_INV_INIT   = 1e-6   # initial 1/Qi(0)  (very small positive number)
B_INIT         = 1e-5   # Kondo coefficient b
TK_INIT        = 0.05   # Kondo temperature T_K  [K]
A_INIT         = 1e-5   # Two Level System

# ── Mattis-Bardeen conductivity ratio ────────────────────────────────────────

def sigma_ratio(T: np.ndarray, f: np.ndarray, Delta_J: float) -> np.ndarray:
    """
    Return σ₁/σ₂ from the Mattis-Bardeen (Nambu) approximation.

    The overall factor (4/π) comes from the ratio of prefactors in eqs. 4 & 5;
    the 4Δ / (ℏω) and πΔ / (ℏω) terms cancel, leaving a pure 4/π coefficient.

    Parameters
    ----------
    T       : temperature [K], shape (N,)
    f       : resonant frequency [Hz], shape (N,)
    Delta_J : superconducting gap at T=0 [J]
    """
    omega = 2.0 * np.pi * f
    xi    = hbar * omega / (2.0 * k_B * T)          # dimensionless, typically ≪ 1

    exp_delta = np.exp(-Delta_J / (k_B * T))         # thermal quasiparticle factor

    # Numerator  ∝  σ₁:  4 * exp(-Δ/kBT) * sinh(ξ) * K₀(ξ)
    # Note: K0 diverges logarithmically as ξ→0, which is fine for ξ > 0.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        num = 4.0 * exp_delta * np.sinh(xi) * kv(0, xi)

    # Denominator  ∝  σ₂:  π * [1 - 2*exp(-Δ/kBT)*exp(-ξ)*I₀(ξ)]
    # I₀(-ξ) = I₀(ξ) because I₀ is an even function.
    den = np.pi * (1.0 - 2.0 * exp_delta * np.exp(-xi) * iv(0, xi))

    # Guard against numerical issues (den ≈ 0 at very high T near Tc)
    den = np.where(np.abs(den) < 1e-30, 1e-30, den)

    return num / den


# ── Fit models ────────────────────────────────────────────────────────────────

def model_plain(X, Qi0_inv, alpha, Delta_meV):
    """
    Model without Kondo correction.

      1/Q_i = 1/Q_i(0) + α * σ₁ / (2σ₂)

    Parameters (free):  Qi0_inv, alpha, Delta_meV
    """
    T, f = X
    Delta_J = Delta_meV * meV
    return Qi0_inv + alpha * sigma_ratio(T, f, Delta_J) / 2.0


def model_kondo(X, Qi0_inv, alpha, Delta_meV, b, T_K):
    """
    Model with Kondo correction.

      1/Q_i = 1/Q_i(0) + α * σ₁ / (2σ₂) - b * ln(T / T_K)

    Parameters (free):  Qi0_inv, alpha, Delta_meV, b, T_K
    """
    T, f = X
    Delta_J = Delta_meV * meV
    return Qi0_inv + alpha * sigma_ratio(T, f, Delta_J) / 2.0 - b * np.log(T / T_K)

def model_TLS(X, Qi0_inv, alpha, Delta_meV, a):
    """
    Model with Kondo correction.

      1/Q_i = 1/Q_i(0) + α * σ₁ / (2σ₂) + a · tanh(ℏω / 2k_BT)

    Parameters (free):  Qi0_inv, alpha, Delta_meV, b, T_K
    """
    T, f = X
    Delta_J = Delta_meV * meV
    omega = 2.0 * np.pi * f
    xi    = hbar * omega / (2.0 * k_B * T) 
    return Qi0_inv + alpha * sigma_ratio(T, f, Delta_J) / 2.0 + a * np.tanh(xi)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, aliases: list[str]) -> str:
    """Return the first column name that matches any alias (case-insensitive)."""
    lower_map = {c.lower(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    raise KeyError(
        f"Could not find a column matching {aliases}. "
        f"Available columns: {list(df.columns)}"
    )


def load_data(path: str):
    """
    Load CSV and return arrays (T [K], f [Hz], Qi_inv [dimensionless]).
    Auto-detects mK→K and GHz→Hz conversions.
    """
    df = pd.read_csv(path, sep=CSV_SEP)
    df.columns = [c.strip() for c in df.columns]

    col_f  = _find_col(df, COL_F_NAMES)
    col_T  = _find_col(df, COL_T_NAMES)
    col_qi = _find_col(df, COL_QI_NAMES)

    f_arr  = df[col_f].to_numpy(dtype=float)
    T_arr  = df[col_T].to_numpy(dtype=float)
    Qi_arr = df[col_qi].to_numpy(dtype=float)

    # Auto-scale units
    """
    if np.median(T_arr) > 10:          # probably mK
        print(f"  [info] Temperature median={np.median(T_arr):.1f} → assuming mK, converting to K")
        T_arr /= 1e3
    if np.median(f_arr) < 1e6:         # probably GHz
        print(f"  [info] Frequency median={np.median(f_arr):.3f} → assuming GHz, converting to Hz")
        f_arr *= 1e9
    """
    T_arr /= 1e3
    Qi_inv = 1.0 / Qi_arr
    #Qi_inv = Qi_arr
    return T_arr, f_arr, Qi_arr, Qi_inv


def chi_squared(y_obs, y_fit, n_params):
    """Reduced chi-squared (assumes Poisson-like errors ~ sqrt(y_obs))."""
    residuals = y_obs - y_fit
    # Simple reduced chi² with uniform uncertainties estimated from RMS
    sigma_est = np.std(residuals)
    if sigma_est == 0:
        return np.nan, residuals
    chi2 = np.sum((residuals / sigma_est) ** 2)
    dof  = len(y_obs) - n_params
    return chi2 / max(dof, 1), residuals


def print_result(label, popt, perr, param_names, chi2_red):
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    for name, val, err in zip(param_names, popt, perr):
        print(f"  {name:<15s} = {val:+.6g}  ±  {err:.3g}")
    print(f"  {'χ²_red':<15s} = {chi2_red:.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    print(f"\nLoading data from: {csv_path}")

    T, f, Qi, Qi_inv = load_data(csv_path)

    N = len(T)
    print(f"  {N} data points loaded")
    print(f"  T range : {T.min()*1e3:.1f} – {T.max()*1e3:.1f} mK")
    print(f"  f range : {f.min()/1e9:.4f} – {f.max()/1e9:.4f} GHz")
    print(f"  Qi range: {Qi.min():.2e} – {Qi.max():.2e}")

    X = (T, f)

    # ── Fit 1: plain Mattis-Bardeen, no Kondo ────────────────────────────────
    p0_plain   = [QI0_INV_INIT, ALPHA_INIT, DELTA_INIT_MEV]
    bounds_plain = (
        [0,    alfa_min,    0.01],   # lower bounds
        [1e-2, alfa_max, 10.0 ],   # upper bounds
    )
    try:
        popt1, pcov1 = curve_fit(
            model_plain, X, Qi_inv,
            p0=p0_plain, bounds=bounds_plain,
            maxfev=20000,
        )
        perr1   = np.sqrt(np.diag(pcov1))
        fit1    = model_plain(X, *popt1)
        chi2_1, res1 = chi_squared(Qi_inv, fit1, len(p0_plain))
        print_result(
            "Model 1 – Mattis-Bardeen (no Kondo)",
            popt1, perr1,
            ["1/Qi(0)", "alpha", "Delta (meV)"],
            chi2_1,
        )
        # Derive Tc via BCS:  2Δ ≈ 3.52 kB Tc
        Tc_bcs = (2.0 * popt1[2] * meV) / (3.52 * k_B)
        dTc    = (2.0 * perr1[2] * meV) / (3.52 * k_B)
        print(f"  {'Tc (BCS)':<15s} = {Tc_bcs:.4f}  ±  {dTc:.4f} K")
        fit1_ok = True
    except Exception as exc:
        print(f"\n  [WARNING] Model 1 fit failed: {exc}")
        fit1_ok = False
        popt1 = perr1 = fit1 = res1 = None

    # ── Fit 2: Mattis-Bardeen + Kondo logarithm ───────────────────────────────
    p0_kondo   = [QI0_INV_INIT, ALPHA_INIT, DELTA_INIT_MEV, B_INIT, TK_INIT]
    bounds_kondo = (
        [0,    alfa_min,    0.01, 0,    1e-4],
        [1e-2, alfa_max, 10.0,  1e-2, 10.0],
    )
    try:
        popt2, pcov2 = curve_fit(
            model_kondo, X, Qi_inv,
            p0=p0_kondo, bounds=bounds_kondo,
            maxfev=50000,
        )
        perr2   = np.sqrt(np.diag(pcov2))
        fit2    = model_kondo(X, *popt2)
        chi2_2, res2 = chi_squared(Qi_inv, fit2, len(p0_kondo))
        print_result(
            "Model 2 – Mattis-Bardeen + Kondo",
            popt2, perr2,
            ["1/Qi(0)", "alpha", "Delta (meV)", "b", "T_K (K)"],
            chi2_2,
        )
        Tc_bcs2 = (2.0 * popt2[2] * meV) / (3.52 * k_B)
        dTc2    = (2.0 * perr2[2] * meV) / (3.52 * k_B)
        print(f"  {'Tc (BCS)':<15s} = {Tc_bcs2:.4f}  ±  {dTc2:.4f} K")
        fit2_ok = True
    except Exception as exc:
        print(f"\n  [WARNING] Model 2 fit failed: {exc}")
        fit2_ok = False
        popt2 = perr2 = fit2 = res2 = None


        # ── Fit 3: Mattis-Bardeen + Two Level System ───────────────────────────────
    p0_tls   = [QI0_INV_INIT, ALPHA_INIT, DELTA_INIT_MEV, A_INIT]
    bounds_tls = (
        [0,    alfa_min,    0.01, 0],
        [1e-2, alfa_max, 10.0,  1e-2],
    )
    try:
        popt3, pcov3 = curve_fit(
            model_TLS, X, Qi_inv,
            p0=p0_tls, bounds=bounds_tls,
            maxfev=50000,
        )
        perr3   = np.sqrt(np.diag(pcov3))
        fit3    = model_TLS(X, *popt3)
        chi2_3, res3 = chi_squared(Qi_inv, fit3, len(p0_tls))
        print_result(
            "Model 3 – Mattis-Bardeen + Two Level System",
            popt3, perr3,
            ["1/Qi(0)", "alpha", "Delta (meV)", "a"],
            chi2_3,
        )
        Tc_bcs3 = (2.0 * popt3[2] * meV) / (3.52 * k_B)
        dTc3    = (2.0 * perr3[2] * meV) / (3.52 * k_B)
        print(f"  {'Tc (BCS)':<15s} = {Tc_bcs3:.4f}  ±  {dTc3:.4f} K")
        fit3_ok = True
    except Exception as exc:
        print(f"\n  [WARNING] Model 3 fit failed: {exc}")
        fit3_ok = False
        popt3 = perr3 = fit3 = res3 = None

    # ── Plot ─────────────────────────────────────────────────────────────────
    T_sort = np.argsort(T)
    T_s    = T[T_sort]
    Qi_inv_s = Qi_inv[T_sort]

    fig, axes = plt.subplots(
        2, 1,
        figsize=(9, 8),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True,
    )
    ax_main, ax_res = axes

    # Data
    ax_main.plot(
        T_s * 1e3, Qi_inv_s,
        "o", ms=4, color="steelblue", alpha=0.7,
        label="Data", zorder=5,
    )

    colors = ["crimson", "darkorange", "green"]
    labels = [
        f"MB, no Kondo  (Δ={popt1[2]:.3f} meV)" if fit1_ok else "MB, no Kondo (failed)",
        f"MB + Kondo    (Δ={popt2[2]:.3f} meV)" if fit2_ok else "MB + Kondo (failed)",
        f"MB + TLS    (Δ={popt3[2]:.3f} meV)" if fit3_ok else "MB + TLS (failed)",
    ]

    if fit1_ok:
        ax_main.plot(T_s * 1e3, fit1[T_sort], "-", lw=2,
                     color=colors[0], label=labels[0])
        ax_res.plot(T_s * 1e3, res1[T_sort], "-o", ms=3,
                    lw=1, color=colors[0], alpha=0.8,
                    label=f"Residuals (no Kondo),  χ²_red={chi2_1:.3f}")

    if fit2_ok:
        ax_main.plot(T_s * 1e3, fit2[T_sort], "--", lw=2,
                     color=colors[1], label=labels[1])
        ax_res.plot(T_s * 1e3, res2[T_sort], "--o", ms=3,
                    lw=1, color=colors[1], alpha=0.8,
                    label=f"Residuals (+ Kondo),    χ²_red={chi2_2:.3f}")
                
    if fit3_ok:
        ax_main.plot(T_s * 1e3, fit3[T_sort], "--", lw=2,
                     color=colors[2], label=labels[2])
        ax_res.plot(T_s * 1e3, res3[T_sort], "--o", ms=3,
                    lw=1, color=colors[2], alpha=0.8,
                    label=f"Residuals (+ TLS),    χ²_red={chi2_3:.3f}")

    ax_res.axhline(0, color="gray", lw=0.8, ls=":")

    ax_main.set_ylabel(r"$1/Q_i$", fontsize=13)
    ax_main.legend(fontsize=10, framealpha=0.9)
    ax_main.grid(True, alpha=0.3)
    ax_main.set_title("MKID Internal Quality Factor vs Temperature", fontsize=13)

    ax_res.set_xlabel("Temperature  (mK)", fontsize=13)
    ax_res.set_ylabel(r"Residuals  $\Delta(1/Q_i)$", fontsize=11)
    ax_res.legend(fontsize=9, framealpha=0.9)
    ax_res.grid(True, alpha=0.3)

    plt.tight_layout()
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    out_fig = Path(csv_path).stem + "_fit.png"
    plt.savefig(f"/Users/Rajmund/Desktop/MKID/{out_fig}", dpi=150, bbox_inches="tight")
    print(f"\nPlot saved → {out_fig}")
    plt.show()


if __name__ == "__main__":
    main()
