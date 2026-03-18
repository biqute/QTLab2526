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

data_file = "cavity_10.335GHz"
save_as = "Fit_"+data_file

# Assumi che il file ../data/misura_S21.txt contenga: freq, real, imag
data = np.loadtxt("data/"+data_file + ".txt", delimiter="\t")
frequencies = data[:, 0]  # Frequenze in Hz
real_S21 = data[:, 1]     # Parte reale di S21
imag_S21 = data[:, 2]     # Parte immaginaria di S21
S21 = real_S21 + 1j * imag_S21

signal = np.abs(S21)
phase = np.angle(S21)

####################################

fitter = CircleFitter()


S21 = signal * np.exp(1j * phase)

#TAU = fitter._guess_delay(frequencies, S21)

#print("initial TAU guess:", TAU)

S21_calibrated = S21 #fitter._remove_cable_delay(frequencies, S21, TAU)

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

phase_centered = np.angle(S21_centered)

angles = np.angle((S21_centered ))
span = np.degrees(np.max(angles)- np.min(angles))
print("Arc span =", span, "degrees")


#-----Phase fit to get resonance----------
f_r_guess, Q_r_guess = fitter._fit_lorentz(S21_calibrated, frequencies)
theta_0_guess = phase_centered[np.argmax(signal)]
theta_0, Q_r, f_r = fitter._fit_phase(S21_centered, frequencies, theta_0_guess, Q_r_guess, f_r_guess)
print("theta_0_guess=", theta_0_guess)
theta_fit = theta_model(frequencies, theta_0, Q_r, f_r)

print ("f_r=", f_r )
print ("theta_0=", theta_0 )
print ("Q_r=", Q_r )


#----Finding P'-----
beta = (theta_0 + np.pi) % (2*np.pi ) - np.pi  #sets beta in (-pi,pi)
P_off = x_c + r_0 * np.cos(beta)  + 1j*(y_c + r_0 * np.sin(beta))
a_scaling = abs(P_off)  #gives amplitude distortion a
alpha = np.angle(P_off) #gives phase ditortion exp(ialpha)

print("angle alpha=", alpha)

print("scaling=", a_scaling)


#---Final circle fit of the canonical form---

x_can, y_can, r_0_can = fitter._fit_from_complex(fitter._canonize(frequencies, S21, a_scaling, alpha, tau_true))

#---Quality factors----
Q_c_mag = Q_r * 2* r_0_can

phi_0 = -np.asin(y_can/r_0_can)

Q_c = Q_r /(2*r_0_can* np.exp( -1j* phi_0 ))

Q_c_rev = 1/Q_c

Q_i_rev = 1/Q_r - Q_c_rev.real

Q_i = 1/Q_i_rev


#---Performing complex fit now-----
S = signal * np.exp(1j * phase)  # complex


S_fit = S21_notch(frequencies, Q_r, np.abs(Q_c), np.angle(Q_c), f_r, a_scaling, alpha, tau_true) #/a_fit * np.exp(+1j* 2*np.pi*(TAU+tau_fit)*frequencies)*np.exp(-1j*alpha_fit)


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
ax_iq.plot(S.real, S.imag, marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
#ax_iq.plot(S_fit.real[::50], S_fit.imag[::50], '-', ms=1.5, label='Fit')
#ax_iq.plot(xcirc, ycirc, '-', ms=1.5, label='ideal circ')
ax_iq.set_aspect('equal', 'box')
ax_iq.axhline(0, color='gray', linewidth=0.8)   # real axis (horizontal)
ax_iq.axvline(0, color='gray', linewidth=0.8)   # imaginary axis (vertical)
ax_iq.set_xlabel(r"$\Re\{S_{21}\}$")          
ax_iq.set_ylabel(r"$\Im\{S_{21}\}$")
#ax_iq.plot([P_off.real], [P_off.imag], "ro", ms = 8, label = "P(1,0)") 
ax_iq.plot([], [], ' ', label=fr"$Q_l = {Q_r:.1f}$") 
ax_iq.plot([], [], ' ', label=fr"$Q_i = {Q_i:.1f}$")         
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

#----Signal plot-----
ax_mag.plot(frequencies/1e9, abs(S),marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
ax_mag.plot(frequencies/1e9, abs(S_fit), '-', ms=1.5, label='Fit')
ax_mag.set_xlabel(r"$f[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

#----Phase plot-------
ax_phase.plot(frequencies/1e9, np.unwrap(np.angle(S21_centered)), marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
ax_phase.plot(frequencies/1e9, theta_model(frequencies, theta_0, Q_r, f_r), '-', lw=2, label='arg(S_{21})')
ax_phase.set_xlabel(r"$f [GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")
ax_phase.legend(loc ="best")

plt.show()