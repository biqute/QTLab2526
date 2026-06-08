import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from iminuit import Minuit
import sys
sys.path.append("../")
from circle_fit import CircleFitter

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica",
    "axes.labelsize": 16,
    "axes.titlesize": 18,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 12,
    "lines.linewidth": 2
})

################ MAIN ########################
# ---------------- Load data ----------------
data = np.loadtxt("../data/acquisizione.txt")
time = data[:, 0] # ns
I = data[:, 1]    # mV
Q = data[:, 2]    # mV

A = 150 # mV

# ------- Mixer Response (Circle Fit Guess) ----
R = Q + 1j*I
fitter = CircleFitter()
x_c, y_c, r_0 = fitter._fit_from_complex(R)

# Calcolo della fase preliminare traslando i dati nel centro stimato
theta_data = np.unwrap(np.arctan2(I - y_c, Q - x_c))

# ============================================
# ---- iminuit Fit ----
# ============================================

def least_squares_cost(I_0, A_I, Q_0, A_Q, Dtheta):
    model_Q = Q_0 + A_Q * np.cos(theta_data + Dtheta)
    model_I = I_0 + A_I * np.sin(theta_data)
    residuals_sq = (Q - model_Q)**2 + (I - model_I)**2
    return np.sum(residuals_sq)

m = Minuit(least_squares_cost, 
           I_0=y_c, A_I=r_0, 
           Q_0=x_c, A_Q=r_0, 
           Dtheta=0.0)

m.errordef = Minuit.LEAST_SQUARES
m.limits["Dtheta"] = (-np.pi, np.pi)

m.migrad()
m.hesse()

popt = m.values

# ============================================
# === APPLICAZIONE DELLA CORREZIONE IQ ===
# ============================================
# Impostiamo l'ampiezza target pari a r_0 per mantenere la stessa scala visiva
A_RO = r_0 

# Centriamo i dati rimuovendo i DC offset calcolati
I_detrend = I - popt["I_0"]
Q_detrend = Q - popt["Q_0"]

# Applichiamo la matrice di calibrazione punto per punto ai dati sperimentali
I_corr = A_RO * (I_detrend / popt["A_I"])
Q_corr = A_RO * (Q_detrend / (popt["A_Q"] * np.cos(popt["Dtheta"])) + (I_detrend / popt["A_I"]) * np.tan(popt["Dtheta"]))

# Generiamo le curve continue ideali per il plot
theta_fit = np.linspace(0, 2*np.pi, 400)
fit_Q = popt["Q_0"] + popt["A_Q"] * np.cos(theta_fit + popt["Dtheta"])
fit_I = popt["I_0"] + popt["A_I"] * np.sin(theta_fit)

ideal_Q = A_RO * np.cos(theta_fit)
ideal_I = A_RO * np.sin(theta_fit)

# ============================================
# === Plot di Confronto (Prima vs Dopo) ===
# ============================================

fig, (ax_raw, ax_corr) = plt.subplots(1, 2, figsize=(14, 6.5))

# --- Grafico 1: Dati Originali e Fit ---
ax_raw.plot(Q, I, marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=6, label="Raw Data")
ax_raw.plot(fit_Q, fit_I, '-', color="red", lw=2.5, label="Ellipse Fit")
ax_raw.plot(popt["Q_0"], popt["I_0"], marker='X', ms=10, color="red", label="Fit Center")

ax_raw.set_xlabel(r"$Q$ (mV)")
ax_raw.set_ylabel(r"$I$ (mV)")
ax_raw.axis('equal')
ax_raw.plot(0, 0, marker='+', ms=12, color='black', label="Origin (0,0)")
ax_raw.grid(True, alpha=0.3)
ax_raw.legend(loc="upper right")
#ax_raw.set_title("Risposta Mixer Originale")

# Riquadro parametri sul grafico di sinistra
textstr = '\n'.join((
    r'\textbf{Fit Parameters:}',
    r'$I_0 = %.2f \pm %.2f$ mV' % (popt["I_0"], m.errors["I_0"]),
    r'$A_I = %.2f \pm %.3f$ mV' % (popt["A_I"], m.errors["A_I"]),
    r'$Q_0 = %.2f \pm %.2f$ mV' % (popt["Q_0"], m.errors["Q_0"]),
    r'$A_Q = %.2f \pm %.3f$ mV' % (popt["A_Q"], m.errors["A_Q"]),
    r'$\Delta\theta = %.4f \pm %.4f$ rad' % (popt["Dtheta"], m.errors["Dtheta"])
))
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5, edgecolor='gray')
ax_raw.text(0.05, 0.95, textstr, transform=ax_raw.transAxes, fontsize=11, verticalalignment='top', bbox=props)


# --- Grafico 2: Dati Corretti (Cerchio Perfetto) ---
ax_corr.plot(Q_corr, I_corr, marker='o', linestyle='', markeredgecolor='navy', markerfacecolor='white', ms=6, label="Corrected Data", alpha=0.85)
ax_corr.plot(ideal_Q, ideal_I, '--', color='darkblue', lw=1.5, label="Ideal Circle")
ax_corr.plot(0, 0, marker='+', ms=12, color='black', label="Origin (0,0)")

ax_corr.set_xlabel(r"$Q_{corr}$ (mV)")
ax_corr.set_ylabel(r"$I_{corr}$ (mV)")
ax_corr.axis('equal')
ax_corr.grid(True, alpha=0.3)
ax_corr.legend(loc="upper right")
#ax_corr.set_title("Risposta Corretta e Centrata")

# Uniformiamo i limiti degli assi per un confronto visivo diretto ed onesto
xlims = ax_raw.get_xlim()
ylims = ax_raw.get_ylim()
# Centriamo i limiti per il grafico di destra attorno a (0,0)
max_range = max(max(abs(np.array(xlims))), max(abs(np.array(ylims))))
ax_corr.set_xlim(-max_range, max_range)
ax_corr.set_ylim(-max_range, max_range)

plt.savefig("../data0_plots/IQ_mixer_calibration.pdf", bbox_inches="tight")
print("Plots saved in ../data0_plots/IQ_mixer_calibration.pdf")
plt.tight_layout()
plt.show()