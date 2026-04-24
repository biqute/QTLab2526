import os
import re
import numpy as np
import pandas as pd
from scipy.constants import k

from resonance_utils import ResonanceKid, GapFinder


# ======================
# UTILS
# ======================

def extract_temperature(folder_name):
    try:
        return float(folder_name.replace("mk", "").replace("_", "."))
    except:
        return None


def extract_peak_name(filename):
    match = re.match(r"(picco\d+)", filename)
    return match.group(1) if match else None


def convert_csv_to_clean_txt(csv_path):
    """
    Legge CSV con pandas e salva file temporaneo pulito
    (solo colonne numeriche, separatore whitespace)
    """
    df = pd.read_csv(csv_path)

    # prendiamo solo colonne utili
    cols = ["frequency", "Re(S21)", "Im(S21)"]
    df = df[cols]

    clean_path = csv_path.replace(".csv", "_clean.txt")

    np.savetxt(clean_path, df.values)

    return clean_path


# ======================
# FIT RESONANCES
# ======================

def fit_all_resonances(basepath, polgrad, fmin, fmax, phase=False, plot=False):

    results = {}

    for folder in os.listdir(basepath):
        folder_path = os.path.join(basepath, folder)

        if not os.path.isdir(folder_path):
            continue

        Tval = extract_temperature(folder)
        if Tval is None:
            continue

        for file in os.listdir(folder_path):
            if not file.endswith(".csv"):
                continue

            peak = extract_peak_name(file)
            if peak is None:
                continue

            csv_path = os.path.join(folder_path, file)

            try:
                # 🔥 FIX: conversione robusta
                filepath = convert_csv_to_clean_txt(csv_path)

                if peak not in results:
                    results[peak] = {
                        "T": [],
                        "invQi": [],
                        "invQiErr": [],
                        "ini": None,
                        "f0": None
                    }

                data = results[peak]

                if data["ini"] is None:
                    res = ResonanceKid(filepath, polyorder=polgrad, fit_phase=phase)
                    res.f0_from_fit()
                    data["f0"] = res.f0_fit
                    res.fit()
                    data["ini"] = np.asarray(res.fit_result.values)
                else:
                    res = ResonanceKid(
                        filepath,
                        polyorder=polgrad,
                        fit_phase=phase,
                        init_parameters=data["ini"]
                    )

                res.set_freq_cut(fmin, fmax)
                res.min_obj = res.minuit_obj()
                res.fit()

                if plot:
                    res.plot_fit()
                    print(f"Fitted: {csv_path}")

                data["T"].append(Tval)
                data["invQi"].append(res.invQvalues[1])
                data["invQiErr"].append(res.invQerrors[1])

                data["ini"] = np.asarray(res.fit_result.values)

            except Exception as e:
                print(f"Error fitting {csv_path}: {e}")

    return results


# ======================
# SAVE
# ======================

def save_results(basepath, results):
    for peak, data in results.items():
        if len(data["T"]) == 0:
            continue

        arr = np.column_stack([
            np.array(data["T"]),
            np.array(data["invQi"]),
            np.array(data["invQiErr"])
        ])

        outfile = os.path.join(basepath, f"{peak}_qi_vs_t.txt")
        np.savetxt(outfile, arr, fmt=['%.2f', '%.6E', '%.6E'])

        print(f"Saved: {outfile}")


# ======================
# GAP FIT
# ======================

def run_gap_fit(basepath, results, Tlim, fit_type):

    FitResult = {}

    for peak, data in results.items():
        filepath = os.path.join(basepath, f"{peak}_qi_vs_t.txt")

        if not os.path.isfile(filepath):
            continue

        try:
            gap_obj = GapFinder(filepath, omega=data["f0"], fit_type=fit_type)
            gap_obj.set_T_limit(Tlim)
            gap_obj.plot_fit()

            delta0 = gap_obj.fit_result.values[0] * 1e-23
            deltaErr = gap_obj.fit_result.errors[0] * 1e-23

            tc = delta0 * (2 / 3.52) / k
            tcErr = deltaErr * (2 / 3.52) / k
            chi = round(gap_obj.chi2(), 3)

            if fit_type == 'kondo':
                TK = gap_obj.fit_result.values[1]
                TKErr = gap_obj.fit_result.errors[1]
                FitResult[peak] = [tc, tcErr, delta0, deltaErr, TK, TKErr, chi]
            else:
                FitResult[peak] = [tc, tcErr, delta0, deltaErr, chi]

            print(f"\n{peak}: Tc = {tc:.5f} ± {tcErr:.5f} K")

        except Exception as e:
            print(f"Gap fit error for {peak}: {e}")

    return FitResult


# ======================
# MAIN
# ======================

if __name__ == "__main__":

    basepath = r"C:\Users\kid\labQT\Lab2025\Single photon\QTLab2526\SinglePhoton\VNA\CRIO_measures_new"

    print("=== FIT RESONANCES ===")
    results = fit_all_resonances(
        basepath=basepath,
        polgrad=2,
        fmin=-0.0015,
        fmax=0.0015,
        plot=False
    )

    print("\n=== SAVE RESULTS ===")
    save_results(basepath, results)

    print("\n=== GAP FIT ===")
    FitResult = run_gap_fit(
        basepath=basepath,
        results=results,
        Tlim=260,
        fit_type='kondo'
    )

    print("\n=== FINAL RESULTS ===")
    for k, v in FitResult.items():
        print(k, ":", v)