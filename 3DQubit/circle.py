import numpy as np
from scipy import optimize
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from circle_fit import CircleFitter

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
data = np.load("data_2.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])

#----Taking a window around the resonance
idx = np.argmin(signal)
print(frequencies[idx])
print(frequencies[idx])
signal = signal#[idx-2500:idx + 2500]
phase = phase#[idx-2500:idx + 2500]
frequencies = frequencies#[idx-2500:idx+2500]

####################################

fitter = CircleFitter()


S21 = signal * np.exp(1j * phase)

TAU = fitter._guess_delay(frequencies, S21)

print("initial TAU guess:", TAU)

S21_calibrated = fitter._remove_cable_delay(frequencies, S21, TAU)

# ---------------- Circle fit via CircleFitter ----------------

tau_true = fitter._fit_delay(frequencies, S21_calibrated)

print("true tau:", tau_true)

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
print("Arc span =", span, "degrees")

#-----Phase fit to get resonance----------
f_r_guess, Q_r_guess = fitter._fit_lorentz(S21_calibrated, frequencies)
theta_0, Q_r, f_r = fitter._fit_phase(S21_centered, frequencies, -4, Q_r_guess, f_r_guess)

theta_fit = theta_model(frequencies, theta_0, Q_r, f_r)

print ("f_r=", f_r )
print ("theta_0=", theta_0 )
print ("Q_r=", Q_r )


#----Finding P'-----
beta = (theta_0 + np.pi) 
P_off = x_c + r_0 * np.cos(beta)  + 1j*(y_c + r_0 * np.sin(beta))
a_scaling = abs(P_off)  #gives amplitude distortion a
alpha = np.angle(P_off) #gives phase ditortion exp(ialpha)

print(alpha)

print(a_scaling)


#---Final circle fit of the canonical form---

x_can, y_can, r_0_can = fitter._fit_from_complex(fitter._canonize(frequencies, S21, a_scaling, alpha, TAU + tau_true))

#---Quality factors----
Q_c_mag = Q_r * 2* r_0_can

phi_0 = -np.asin(y_can/r_0_can)

Q_c = Q_r /(2*r_0_can* np.exp( -1j* phi_0 ))

Q_c_rev = 1/Q_c

Q_i_rev = 1/Q_r - Q_c_rev.real

Q_i = 1/Q_i_rev


#---Performing complex fit now-----
S = signal * np.exp(1j * phase)  # complex

ydata = np.hstack([S.real, S.imag])

params, pcov = fitter._fit_notch(S, frequencies, Q_r, Q_c, f_r, a_scaling, alpha, TAU + tau_true)


Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit = params

Qc_fit= abs_Qc_fit * np.exp(-1j * phase_Qc_fit)

Qc_fit_rev= 1/Qc_fit

Qi_fit_rev = 1/Ql_fit - Qc_fit_rev.real

Qi_fit = 1/Qi_fit_rev

print("Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit =", params)

print("cov matrix:", pcov)


S_fit = S21_notch(frequencies, Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit) #/a_fit * np.exp(+1j* 2*np.pi*(TAU+tau_fit)*frequencies)*np.exp(-1j*alpha_fit)
S_canonized = fitter._canonize(frequencies, S, a_fit, alpha_fit, TAU+tau_fit)


#------Residuals-------

residuals = S - S_fit



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
ax_iq.plot(S.real[::50], S.imag[::50], marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
ax_iq.plot(S_fit.real[::50], S_fit.imag[::50], '-', ms=1.5, label='Fit')
#ax_iq.plot(xcirc, ycirc, '-', ms=1.5, label='ideal circ')
ax_iq.set_aspect('equal', 'box')
ax_iq.axhline(0, color='gray', linewidth=0.8)   # real axis (horizontal)
ax_iq.axvline(0, color='gray', linewidth=0.8)   # imaginary axis (vertical)
ax_iq.set_xlabel(r"$\Re\{S_{21}\}$")          
ax_iq.set_ylabel(r"$\Im\{S_{21}\}$")
#ax_iq.plot([P_off.real], [P_off.imag], "ro", ms = 8, label = "P(1,0)") 
ax_iq.plot([], [], ' ', label=fr"$Q_l = {Ql_fit:.1f}$") 
ax_iq.plot([], [], ' ', label=fr"$Q_i = {Qi_fit:.1f}$")         
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

#----Signal plot-----
ax_mag.plot(frequencies[::150]/1e9, abs(S)[::150],marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
ax_mag.plot(frequencies/1e9, abs(S_fit), '-', ms=1.5, label='Fit')
ax_mag.set_xlabel(r"$f[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

#----Phase plot-------
ax_phase.plot(frequencies[::200]/1e9, np.unwrap(np.angle(S))[::200], marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
ax_phase.plot(frequencies/1e9, np.unwrap(np.angle(S_fit)), '-', lw=2, label='arg(S_{21})')
ax_phase.set_xlabel(r"$f [GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")
ax_phase.legend(loc ="best")

plt.show()