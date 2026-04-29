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
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import kv, iv
from pathlib import Path
from datetime import datetime

# ── Physical constants ────────────────────────────────────────────────────────
k_B  = 1.380649e-23   # J / K
hbar = 1.054571817e-34 # J·s
eV   = 1.602176634e-19 # J / eV
meV  = eV * 1e-3       # J / meV

# ── Configuration – edit these if needed ─────────────────────────────────────
DEFAULT_CSV  = "data/p1_all.csv"          # fallback filename
CSV_SEP      = ","                 # column separator
# Fixed CSV column names (exact, case-insensitive)
COL_F   = "f"
COL_T   = "t"
COL_QI  = "Q_i"

# Pixel identification: resonant frequency [GHz] → pixel label
# Each entry covers ± PIXEL_TOL_GHz around the listed centre frequency.
PIXEL_FREQS = {
    1: 7.49,
    2: 7.81,
    3: 7.99,
    4: 8.39,
    5: 8.63,
}
PIXEL_TOL_GHz = 0.10   # tolerance window around each centre [GHz]
Q_MAX = 1e6

# Initial guess ranges for the fit parameters
alfa_sim       = 0.734    # simulated kinetic inductance fraction (0 < α < 1)
alfa_min = alfa_sim * 0.90 # lower bound
alfa_max = min(alfa_sim * 1.2, 0.99) # upper bound
# Δ is expressed in meV throughout the fitting to keep numbers ~O(1).
DELTA_INIT_MEV = 0.40   # initial guess for energy gap  [meV]
ALPHA_INIT     = alfa_sim    # kinetic inductance fraction (0 < α < 1)
#QI0_INV_INIT   = 1e-6   # initial 1/Qi(0)  (very small positive number)
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

def identify_pixel(f_GHz: float) -> str:
    """Return 'Pixel N' for the first matching entry, or 'Unknown pixel'."""
    for px, centre in PIXEL_FREQS.items():
        if abs(f_GHz - centre) <= PIXEL_TOL_GHz:
            return f"Pixel {px}"
    return f"Unknown pixel  (f_r = {f_GHz:.4f} GHz)"


def load_data(path: str):
    df = pd.read_csv(path, sep=CSV_SEP)
    df.columns = [c.strip() for c in df.columns]

    lower_map = {c.lower(): c for c in df.columns}
    try:
        T_arr  = df[lower_map[COL_T.lower()]].to_numpy(dtype=float)
        f_arr  = df[lower_map[COL_F.lower()]].to_numpy(dtype=float)
        Qi_arr = df[lower_map[COL_QI.lower()]].to_numpy(dtype=float)
    except KeyError as e:
        raise KeyError(
            f"Expected column {e} not found.  "
            f"Available columns: {list(df.columns)}"
        )

    T_arr /= 1e3                        # mK → K  (always)

    # Auto-detect frequency unit: if median > 1e6 the column is already in Hz
    if np.median(f_arr) > 1e6:
        print(f"  [info] f median = {np.median(f_arr):.3e} → assuming Hz")
    else:
        print(f"  [info] f median = {np.median(f_arr):.4f} → assuming GHz, converting to Hz")
        f_arr *= 1e9

    f_GHz = float(np.median(f_arr)) / 1e9   # always derived after normalisation

    pixel_label = identify_pixel(f_GHz)
    Qi_inv = 1.0 / Qi_arr
    return T_arr, f_arr, Qi_arr, Qi_inv, pixel_label


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


def print_result(label, popt, perr, param_names, chi2_red, Qi_min_measured):
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    for name, val, err in zip(param_names, popt, perr):
        if name == "1/Qi(0)":
            # Convert to Q(0) and propagate uncertainty: σ_Q = σ_(1/Q) / (1/Q)²
            Q0     = 1.0 / val
            dQ0    = err / (val ** 2)
            status = "✓ OK" if Q0 > Qi_min_measured else "✗ UNPHYSICAL (Q(0) < Q(T_min))"
            print(f"  {'Q(0)':<15s} = {Q0:.0f}  ±  {dQ0:.0f}    {status}")
        else:
            print(f"  {name:<15s} = {val:+.6g}  ±  {err:.3g}")
    print(f"  {'χ²_red':<15s} = {chi2_red:.4f}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    print(f"\nLoading data from: {csv_path}")

    T, f, Qi, Qi_inv, pixel_label = load_data(csv_path)

    # Q_i at the lowest measured temperature — used to sanity-check Q(0)
    Qi_at_Tmin = float(Qi[np.argmin(T)])
    Q_MIN = Qi_at_Tmin * 0.99
    QI0_INV_INIT = 1/Qi_at_Tmin

    N = len(T)
    print(f"  {N} data points loaded")
    print(f"  Pixel      : {pixel_label}")
    print(f"  T range    : {T.min()*1e3:.1f} – {T.max()*1e3:.1f} mK")
    print(f"  f range    : {f.min()/1e9:.4f} – {f.max()/1e9:.4f} GHz")
    print(f"  Qi range   : {Qi.min():.2e} – {Qi.max():.2e}")
    print(f"  Qi(T_min)  : {Qi_at_Tmin:.0f}  (Q(0) must exceed this)")

    X = (T, f)

    # ── Fit 1: plain Mattis-Bardeen ────────────────────────────────
    p0_plain   = [QI0_INV_INIT, ALPHA_INIT, DELTA_INIT_MEV]
    bounds_plain = (
        [1/Q_MAX,    alfa_min,    0.01],
        [1/Q_MIN, alfa_max, 10.0],   # Q(0) must be > Q(T_min)
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
            "Model 1 – Mattis-Bardeen ",
            popt1, perr1,
            ["1/Qi(0)", "alpha", "Delta (meV)"],
            chi2_1, Qi_at_Tmin,
        )
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
        [1/Q_MAX,    alfa_min,    0.01, 0,    1e-4],
        [1/Q_MIN, alfa_max, 10.0, 1e-2, 10.0],
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
            chi2_2, Qi_at_Tmin,
        )
        Tc_bcs2 = (2.0 * popt2[2] * meV) / (3.52 * k_B)
        dTc2    = (2.0 * perr2[2] * meV) / (3.52 * k_B)
        print(f"  {'Tc (BCS)':<15s} = {Tc_bcs2:.4f}  ±  {dTc2:.4f} K")
        fit2_ok = True
    except Exception as exc:
        print(f"\n  [WARNING] Model 2 fit failed: {exc}")
        fit2_ok = False
        popt2 = perr2 = fit2 = res2 = None

    # ── Fit 3: Mattis-Bardeen + Two Level System ──────────────────────────────
    p0_tls   = [QI0_INV_INIT, ALPHA_INIT, DELTA_INIT_MEV, A_INIT]
    bounds_tls = (
        [1/Q_MAX,    alfa_min,    0.01, 0],
        [1/Q_MIN, alfa_max, 10.0, 1e-2],
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
            chi2_3, Qi_at_Tmin,
        )
        Tc_bcs3 = (2.0 * popt3[2] * meV) / (3.52 * k_B)
        dTc3    = (2.0 * perr3[2] * meV) / (3.52 * k_B)
        print(f"  {'Tc (BCS)':<15s} = {Tc_bcs3:.4f}  ±  {dTc3:.4f} K")
        fit3_ok = True
    except Exception as exc:
        print(f"\n  [WARNING] Model 3 fit failed: {exc}")
        fit3_ok = False
        popt3 = perr3 = fit3 = res3 = None

    # ── Save results to JSON ──────────────────────────────────────────────────
    stem     = Path(csv_path).stem
    json_path = Path(csv_path).parent / (stem + "_fit_results.json")

    def _pack(popt, perr, names, chi2):
        """Build a tidy dict for one model, converting 1/Q(0) → Q(0)."""
        d = {"chi2_red": round(float(chi2), 5)}
        for name, val, err in zip(names, popt, perr):
            if name == "1/Qi(0)":
                d["Q0"]      = round(1.0 / float(val), 1)
                d["Q0_err"]  = round(float(err) / float(val)**2, 1)
            else:
                d[name]          = float(val)
                d[name + "_err"] = float(err)
        return d

    results = {
        "file":   csv_path,
        "pixel":  pixel_label,
        "Qi_at_Tmin": round(Qi_at_Tmin, 1),
    }
    if fit1_ok:
        results["model_MB"] = _pack(
            popt1, perr1, ["1/Qi(0)", "alpha", "Delta (meV)"], chi2_1)
    if fit2_ok:
        results["model_MB_Kondo"] = _pack(
            popt2, perr2, ["1/Qi(0)", "alpha", "Delta (meV)", "b", "T_K (K)"], chi2_2)
    if fit3_ok:
        results["model_MB_TLS"] = _pack(
            popt3, perr3, ["1/Qi(0)", "alpha", "Delta (meV)", "a"], chi2_3)

    with open(json_path, "w") as jf:
        json.dump(results, jf, indent=2)
    print(f"\nFit results saved → {json_path}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    SCALE = 1e4          # y-axis multiplier: display 1/Qi × 10⁴
    T_sort   = np.argsort(T)
    T_s      = T[T_sort]
    Qi_inv_s = Qi_inv[T_sort] * SCALE

    fig, axes = plt.subplots(
        2, 1,
        figsize=(9, 8),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True,
    )
    ax_main, ax_res = axes

    ax_main.plot(
        T_s * 1e3, Qi_inv_s,
        "o", ms=4, color="steelblue", alpha=0.7,
        label="Data", zorder=5,
    )

    colors = ["crimson", "darkorange", "green"]
    labels = [
        f"MB  (Δ={popt1[2]:.3f} meV, α={popt1[1]:.3f})"        if fit1_ok else "MB (failed)",
        f"MB + Kondo  (Δ={popt2[2]:.3f} meV, α={popt2[1]:.3f})" if fit2_ok else "MB + Kondo (failed)",
        f"MB + TLS    (Δ={popt3[2]:.3f} meV, α={popt3[1]:.3f})" if fit3_ok else "MB + TLS (failed)",
    ]

    if fit1_ok:
        ax_main.plot(T_s * 1e3, fit1[T_sort] * SCALE, "-", lw=2,
                     color=colors[0], label=labels[0])
        ax_res.plot(T_s * 1e3, res1[T_sort] * SCALE, "-o", ms=3,
                    lw=1, color=colors[0], alpha=0.8,
                    label=f"Residuals,  χ²_red={chi2_1:.3f}")

    if fit2_ok:
        ax_main.plot(T_s * 1e3, fit2[T_sort] * SCALE, "--", lw=2,
                     color=colors[1], label=labels[1])
        ax_res.plot(T_s * 1e3, res2[T_sort] * SCALE, "--o", ms=3,
                    lw=1, color=colors[1], alpha=0.8,
                    label=f"Residuals (+ Kondo),    χ²_red={chi2_2:.3f}")

    if fit3_ok:
        ax_main.plot(T_s * 1e3, fit3[T_sort] * SCALE, "--", lw=2,
                     color=colors[2], label=labels[2])
        ax_res.plot(T_s * 1e3, res3[T_sort] * SCALE, "--o", ms=3,
                    lw=1, color=colors[2], alpha=0.8,
                    label=f"Residuals (+ TLS),      χ²_red={chi2_3:.3f}")

    ax_res.axhline(0, color="gray", lw=0.8, ls=":")

    ax_main.set_ylabel(r"$1/Q_i \; (\times 10^{-4})$", fontsize=13)
    ax_main.legend(fontsize=10, framealpha=0.9)
    ax_main.grid(True, alpha=0.3)
    ax_main.set_title(
        f"MKID Internal Quality Factor vs Temperature  –  {pixel_label}", fontsize=13)

    ax_res.set_xlabel("Temperature  (mK)", fontsize=13)
    ax_res.set_ylabel(r"Residuals  $(\times 10^{-4})$", fontsize=11)
    ax_res.legend(fontsize=9, framealpha=0.9)
    ax_res.grid(True, alpha=0.3)

    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_fig   = f"{stem}_{timestamp}_fit.png"
    #out_fig  = stem + "_fit.png"
    fig_dir  = Path("/Users/Rajmund/Desktop/MKID/figures")
    plt.savefig(fig_dir / out_fig, dpi=150, bbox_inches="tight")
    print(f"Plot saved       → {fig_dir / out_fig}")
    plt.show()


if __name__ == "__main__":
    main()
