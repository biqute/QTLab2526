import numpy as np
from scipy import optimize
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from circle_fit import CircleFitter
import sys
sys.path.append("/")
########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})


#---Phase fit to get resonance f------
def theta_model(f, theta0, Qr, fr):
    return theta0 + 2*np.arctan( 2*Qr*(1.0 - f/fr) )

#---Complex model S21 notch----------

def S21_notch(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau):
    mod_QC = abs_Qc
    phi = phase_Qc
    return a * np.exp(1j*alpha)*np.exp(-1j* 2*np.pi*tau * f) * (1 - ((Ql/mod_QC) * np.exp(1j *phi))/(1 + 2j *Ql*(f/f0 -1)))

################ MAIN ########################
# ---------------- Load data ----------------

n_misura = "0"
data_file = "data_10mK_" + n_misura
save_as = "fit" + n_misura


# Assumi che il file ../data/misura_S21.txt contenga: freq, real, imag
data = np.loadtxt("10mK_resonances/data_10mK/"+data_file + ".txt", delimiter="\t")
frequencies = data[:, 0]  # Frequenze in Hz

real_S21 = data[:, 1]     # Parte reale di S21
imag_S21 = data[:, 2]     # Parte immaginaria di S21

signal = np.abs(real_S21 + 1j * imag_S21)
phase = np.unwrap(np.angle(real_S21 + 1j * imag_S21))


####################################

fitter = CircleFitter()


S21 = signal * np.exp(1j * phase)

TAU = fitter._guess_delay(frequencies, S21)

#print("initial TAU guess:", TAU)

S21_calibrated = fitter._remove_cable_delay(frequencies, S21, TAU)

# ---------------- Circle fit via CircleFitter ----------------

tau_true = fitter._fit_delay(frequencies, S21_calibrated)

#print("true tau:", tau_true)

S21_calibrated = fitter._remove_cable_delay(frequencies, S21_calibrated, tau_true)

#------Ideal circle-----
x_c, y_c, r_0 = fitter._fit_from_complex(S21_calibrated)

theta = np.linspace(0, 2*np.pi, 400)
xcirc = r_0 * np.cos(theta) +x_c
ycirc = r_0 * np.sin(theta) +y_c



#------Translating to the origin---
S21_centered = fitter._center(S21_calibrated, x_c, y_c)

real_S21 = S21_centered.real 
imag_S21 = S21_centered.imag

phase_centered = np.unwrap(np.angle(S21_centered))

angles = np.angle((S21_centered ))
span = np.degrees(np.max(np.unwrap(angles)) - np.min(np.unwrap(angles)))
'''print("Arc span =", span, "degrees")'''

#-----Phase fit to get resonance----------
f_r_guess, Q_r_guess = fitter._fit_lorentz(S21_calibrated, frequencies)
theta_0, Q_r, f_r = fitter._fit_phase(S21_centered, frequencies, phase[np.argmin(signal)], Q_r_guess, f_r_guess)

theta_fit = theta_model(frequencies, theta_0, Q_r, f_r)

'''print ("f_r=", f_r )
print ("theta_0=", theta_0 )
print ("Q_r=", Q_r )'''


#----Finding P'-----
beta = (theta_0 + np.pi) 
P_off = x_c + r_0 * np.cos(beta)  + 1j*(y_c + r_0 * np.sin(beta))
a_scaling = abs(P_off)  #gives amplitude distortion a
alpha = np.angle(P_off) #gives phase ditortion exp(ialpha)

'''print(alpha)

print(a_scaling)'''


#---Final circle fit of the canonical form---

x_can, y_can, r_0_can = fitter._fit_from_complex(fitter._canonize(frequencies, S21, a_scaling, alpha, TAU + tau_true))

#---Quality factors----
Q_c_mag = Q_r * 2* r_0_can

phi_0 = -np.asin(y_can/r_0_can)

Q_c = Q_r /(2*r_0_can* np.exp( -1j* phi_0 ))

Q_c_rev = 1/Q_c

Q_i_rev = 1/Q_r - Q_c_rev.real

Q_i = 1/Q_i_rev

'''print("Q_r =", Q_r)
print("Q_i =", Q_i)
print("Q_c =", Q_c)
print("f_r =", f_r)
print("alpha =", alpha)
print("a =", a_scaling)
print("tau =", TAU + tau_true)
print("abs_Qc =", abs(Q_c))
print("phase_Qc =", np.angle(Q_c))'''


#---Performing complex fit now-----
S = signal * np.exp(1j * phase)  # complex

ydata = np.hstack([S.real, S.imag])

params, pcov = fitter._fit_notch(S, frequencies, Q_r, Q_c, f_r, a_scaling, alpha, TAU + tau_true)


Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit = params

Qc_fit= abs_Qc_fit * np.exp(-1j * phase_Qc_fit)

Qc_fit_rev= 1/Qc_fit

Qi_fit_rev = 1/Ql_fit - Qc_fit_rev.real

Qi_fit = 1/Qi_fit_rev

#print("Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit =", params)

print("f_res =", f0_fit/1e9)
print("Q_i =", Qi_fit)
print("Q_c_abs =", abs_Qc_fit)
print("Q_c_real=", Qc_fit.real)
print("Q_c_imag=", Qc_fit.imag)

#print("cov matrix:", pcov)


S_fit = S21_notch(frequencies, Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit) #/a_fit * np.exp(+1j* 2*np.pi*(TAU+tau_fit)*frequencies)*np.exp(-1j*alpha_fit)
S_canonized = fitter._canonize(frequencies, S, a_fit, alpha_fit, TAU+tau_fit)


#------Residuals-------

residuals = S - S_fit


#-----Q vs f_r 

#Q_val_dep = open("data/Q_vs_fr.txt", "a")
#Q_val_dep.write(f"{f_r/1e9}\t{Q_i}\n")
#Q_val_dep.close()


#---Plot section----

fig = plt.figure(figsize=(10, 6), constrained_layout=True) # --Layout: big left (IQ), right (mag, phase)

gs = GridSpec(
    2, 2, figure=fig,
    width_ratios=[2.7, 1.3],  # big left vs small right
    height_ratios=[1, 1],
    wspace=0.01,               # gap between left and right
    hspace=0.05,               # vertical spacing between small plots
    left=1.2,                 # left margin
    right=1.5,                 # right margin — increase for more border space
    bottom=0.1, top=0.92       # vertical margins
)

ax_iq    = fig.add_subplot(gs[:, 0])  # spans both rows on the left
ax_mag   = fig.add_subplot(gs[0, 1])  # top-right
ax_phase = fig.add_subplot(gs[1, 1])  # bottom-right

# ---- IQ plot ----
ax_iq.plot(S.real, S.imag, 
           marker='o', linestyle='', 
           markeredgecolor='blue', markerfacecolor='white', 
           ms=8, label='Data')
ax_iq.plot(S_fit.real, S_fit.imag, '-', ms=1.5, label='Fit')
#ax_iq.plot(xcirc, ycirc, '-', ms=1.5, label='ideal circ')
ax_iq.set_aspect('equal', 'box')
ax_iq.axhline(0, color='gray', linewidth=0.8)   # real axis (horizontal)
ax_iq.axvline(0, color='gray', linewidth=0.8)   # imaginary axis (vertical)
ax_iq.set_xlabel(r"$Q$", fontsize=12)          
ax_iq.set_ylabel(r"$I$", fontsize=12)
#ax_iq.plot([P_off.real], [P_off.imag], "ro", ms = 8, label = "P(1,0)") 
ax_iq.plot([], [], ' ', label=fr"$Q_l = {Ql_fit:.1f}$") 
ax_iq.plot([], [], ' ', label=fr"$Q_i = {Qi_fit:.1f}$")         
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

#----Signal plot-----
ax_mag.plot(frequencies/1e9, abs(S),marker='o', linestyle='', linewidth = 2 ,markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax_mag.plot(frequencies/1e9, abs(S_fit), '-', ms=1.5, label='Fit')
ax_mag.set_xlabel("Frequency (GHz)", fontsize=12)
ax_mag.set_ylabel(r"$|S_{21}|$", fontsize=12)
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")
ax_mag.legend(loc ="best")
#----Phase plot-------
ax_phase.plot(frequencies/1e9, np.unwrap(np.angle(S)), marker='o', linestyle='', linewidth = 2, markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax_phase.plot(frequencies/1e9, np.unwrap(np.angle(S_fit)), '-', lw=2, label='Fit')
ax_phase.set_xlabel("Frequency (GHz)", fontsize=12)
ax_phase.set_ylabel(r"$\phi$ (rad)", fontsize=12)
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")
ax_phase.legend(loc ="best")

save_as += ".pdf"
fig.savefig(f"10mK_resonances/plots_10mK/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../10mK_resonances/plots_10mK/{save_as}")

'''
# =============================================================================
# --- Plot Separati ---
# =============================================================================

# Otteniamo il nome base senza l'estensione .pdf appena aggiunta
base_save_name = save_as.replace(".pdf", "")
save_path_dir = "10mK_resonances/plots_10mK"

# 1. IQ Plot Separato
fig_iq = plt.figure(figsize=(6, 6))
ax_iq_sep = fig_iq.add_subplot(111)
ax_iq_sep.plot(S.real, S.imag, marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax_iq_sep.plot(S_fit.real, S_fit.imag, '-', ms=1.5, label='Fit')
ax_iq_sep.set_aspect('equal', 'box')
ax_iq_sep.axhline(0, color='gray', linewidth=0.8)
ax_iq_sep.axvline(0, color='gray', linewidth=0.8)
ax_iq_sep.set_xlabel(r"$Q$")
ax_iq_sep.set_ylabel(r"$I$")
ax_iq_sep.plot([], [], ' ', label=fr"$Q_l = {Ql_fit:.1f}$") 
ax_iq_sep.plot([], [], ' ', label=fr"$Q_i = {Qi_fit:.1f}$")         
ax_iq_sep.legend(loc='best')
ax_iq_sep.set_title(r"I-Q Plot")

name_iq = f"{base_save_name}_IQ.pdf"
fig_iq.savefig(f"{save_path_dir}/{name_iq}", bbox_inches="tight")
print(f"Grafico IQ salvato in {save_path_dir}/{name_iq}")

# 2. Magnitude Plot Separato
fig_mag = plt.figure(figsize=(7, 5))
ax_mag_sep = fig_mag.add_subplot(111)
ax_mag_sep.plot(frequencies/1e9, abs(S), marker='o', linestyle='', linewidth=2, markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax_mag_sep.plot(frequencies/1e9, abs(S_fit), '-', ms=1.5, label='Fit')
ax_mag_sep.set_xlabel("Frequency (GHz)")
ax_mag_sep.set_ylabel(r"$|S_{21}|$")
ax_mag_sep.grid(True, alpha=0.3)
ax_mag_sep.set_title("Magnitude")
ax_mag_sep.legend(loc="best")

name_mag = f"{base_save_name}_mag.pdf"
fig_mag.savefig(f"{save_path_dir}/{name_mag}", bbox_inches="tight")
print(f"Grafico Magnitudine salvato in {save_path_dir}/{name_mag}")

# 3. Phase Plot Separato
fig_phase = plt.figure(figsize=(7, 5))
ax_phase_sep = fig_phase.add_subplot(111)
ax_phase_sep.plot(frequencies/1e9, np.unwrap(np.angle(S)), marker='o', linestyle='', linewidth=2, markeredgecolor='blue', markerfacecolor='white', ms=8, label='Data')
ax_phase_sep.plot(frequencies/1e9, np.unwrap(np.angle(S_fit)), '-', lw=2, label='Fit')
ax_phase_sep.set_xlabel("Frequency (GHz)")
ax_phase_sep.set_ylabel(r"$\phi$ (rad)")
ax_phase_sep.grid(True, alpha=0.3)
ax_phase_sep.set_title("Phase")
ax_phase_sep.legend(loc="best")

name_phase = f"{base_save_name}_phase.pdf"
fig_phase.savefig(f"{save_path_dir}/{name_phase}", bbox_inches="tight")
print(f"Grafico Fase salvato in {save_path_dir}/{name_phase}")
'''
plt.show() 

