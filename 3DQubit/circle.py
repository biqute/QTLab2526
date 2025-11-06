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

######### CONSTANTS ############

TAU = 4.000467548463284e-05 #From data.npz
#TAU =4.009328078880438e-05  #From data_2.npz

############# FIT FUNCTIONS ################

#---Phase fit to get resonance f------
def theta_model(f, theta0, Qr, fr):
    return theta0 + 2*np.arctan( 2*Qr*(1.0 - f/fr) )

def phase_residuals(p, f, theta):
    theta0, Qr, fr = p
    return theta_model(f, theta0, Qr, fr) - theta

#---Complex model S21 notch----------

def S21_notch(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau):
    mod_QC = abs_Qc
    phi = phase_Qc
    return a * np.exp(1j*alpha)*np.exp(1j* 2*np.pi*tau * f) * (1 - ((Ql/mod_QC) * np.exp(1j *phi))/(1 + 2j *Ql*(f/f0 -1)))

def S21_notch_real(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau):
    z = S21_notch(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau)
    return np.hstack([z.real, z.imag])

################ MAIN ########################
# ---------------- Load data ----------------
data = np.load("data_0.npz")
frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])

#----Taking a window around the resonance
idx = np.argmin(signal)
print(frequencies[idx])
print(frequencies[idx-1000])
signal = signal[idx-1000:idx + 3000]
phase = phase[idx-1000:idx + 3000]
frequencies = frequencies[idx-1000:idx+3000]


S21 = signal * np.exp(1j * phase)*np.exp(-1j*2*np.pi*frequencies*TAU)

# ---------------- Circle fit via CircleFitter ----------------

fitter = CircleFitter()

res_circ = least_squares(
    lambda t: fitter.residuals_tau(frequencies, S21, t[0]),
    x0=[TAU],
    bounds=(1e-2*TAU, 1e2*TAU)
)

tau_true = res_circ.x[0]

print("true tau:", tau_true)

S21_calibrated = signal * np.exp(1j * phase)*np.exp(-1j*2*np.pi*frequencies*tau_true)


#---Checks---

print("x0:", TAU)
print("x*:", res_circ.x)            # fitted tau
print("nfev:", res_circ.nfev)       # number of residual evaluations
print("cost:", res_circ.cost)       # 0.5 * sum(residuals**2)
print("status:", res_circ.status)
print("message:", res_circ.message)


#------Ideal circle-----
x_c, y_c, r_0 = fitter.fit_from_complex(S21_calibrated)

theta = np.linspace(0, 2*np.pi, 400)
xcirc = r_0 * np.cos(theta)
ycirc = r_0 * np.sin(theta)


#------Translating to the origin---
S21_centered = S21_calibrated - x_c - 1j* y_c

real_S21 = S21_centered.real 
imag_S21 = S21_centered.imag

phase_centered = np.unwrap(np.angle(S21_centered))

angles = np.angle((S21_centered ))
span = np.degrees(np.max(np.unwrap(angles)) - np.min(np.unwrap(angles)))
print("Arc span =", span, "degrees")

#-----Phase fit to get resonance----------
print (np.asin(y_c/r_0))
fr0 = 7574662954.98695 #from lorentzian fit
theta0_0 = 0
Qr0 = fr0/1517610.169032476 #from Lorentzian fit FWHM

print(Qr0)


p0 = [theta0_0, Qr0, fr0] #initial guess

res_fase = least_squares(
    lambda p: phase_residuals(p, frequencies, phase_centered),
    x0=p0,
    bounds=([-10*np.pi,     Qr0/5,     frequencies.min()],        #Qr0/5, Qr0*5 works for data.npz!!!!!
            [ 10*np.pi, Qr0*5, frequencies.max()])
)

theta_0, Q_r, f_r = res_fase.x

theta_fit = theta_model(frequencies, theta_0, Q_r, f_r)

print ("f_r=", f_r )
print ("theta_0=", theta_0 )
print ("Q_r=", Q_r )


#----Finding P'-----
beta = (theta_0 + np.pi) 
P_off = x_c + r_0 * np.cos(beta)  + 1j*(y_c + r_0 * np.sin(beta))
a_scaling = abs(P_off)  #gives amplitude distortion a
alpha = np.angle(P_off) #gives phase ditortion exp(ialpha)

print(a_scaling)


#---Canonical form of S_21---

S21_final = S21_calibrated/a_scaling * np.exp(-1j*alpha)

real_S21_final = S21_final.real
imag_S21_final = S21_final.imag

phase_final = np.unwrap(np.angle(S21_final))
signal_final = abs(S21_final)


#---Final circle fit of the canonical form---

x_can, y_can, r_0_can = fitter.fit_from_complex(S21_final)

theta_can = np.linspace(0, 2*np.pi, 400)
xcirc_can = x_can + r_0_can * np.cos(theta)
ycirc_can = y_can + r_0_can * np.sin(theta)


#---Quality factors----
Q_c_mag = Q_r * 2* r_0_can

phi_0 = -np.asin(y_can/r_0_can)

Q_c = Q_r /(2*r_0_can* np.exp( -1j* phi_0 ))

Q_c_real = Q_c.real

Q_i_rev = 1/Q_r - 1/Q_c_real

Q_i = 1/Q_i_rev

print("Internal Quality Factor Q_i =", Q_i)


#---Performing complex fit now-----
S = signal * np.exp(1j * phase)  # complex

ydata = np.hstack([S.real, S.imag])

abs_Qc = abs(Q_c)
phase_Qc = np.angle(Q_c)

p0 = [Q_r, abs_Qc, phase_Qc, f_r, a_scaling, alpha, tau_true] #params from circle fit

# Bounds 
lower = [1e-2*Q_r,   1e-2*abs_Qc,   -np.pi,  f_r*0.9,  a_scaling/2, -np.pi,  tau_true*0.01]
upper = [1e3*Q_r,  1e3*abs_Qc,   np.pi,  f_r*1.2,  a_scaling*2, np.pi,  tau_true*100 ]

popt, pcov = curve_fit(S21_notch_real, frequencies, ydata, p0=p0, bounds=(lower, upper))

Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit = popt

Qc_fit= abs_Qc_fit * np.exp(1j * phase_Qc_fit)

Qc_fit_real= Qc_fit.real

Qi_fit_rev = 1/Ql_fit - 1/Qc_fit_real

Qi_fit = 1/Qi_fit_rev

print("Ql      =", Ql_fit)
print("Qi    =", Qi_fit)
print("f0      =", f0_fit)
print("a       =", a_fit)
print("alpha   =", alpha_fit)
print("tau     =", tau_fit)

S_fit = S21_notch(frequencies, Ql_fit, abs_Qc_fit, phase_Qc_fit, f0_fit, a_fit, alpha_fit, tau_fit) #/a_fit * np.exp(-1j* 2*np.pi*tau_fit*frequencies)*np.exp(-1j*alpha_fit)
S_canonized = S #/a_fit * np.exp(-1j* 2*np.pi*tau_fit*frequencies)*np.exp(-1j*alpha_fit)
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
ax_iq.plot(S_canonized.real[::30], S_canonized.imag[::30], marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8, label='Raw Data')
ax_iq.plot(S_fit.real[::30], S_fit.imag[::30], '-', ms=1.5, label='Fit')
ax_iq.set_aspect('equal', 'box')
ax_iq.axhline(0, color='gray', linewidth=0.8)   # real axis (horizontal)
ax_iq.axvline(0, color='gray', linewidth=0.8)   # imaginary axis (vertical)
ax_iq.set_xlabel(r"$\Re\{S_{21}\}$")          
ax_iq.set_ylabel(r"$\Im\{S_{21}\}$")
#ax_iq.plot([1], [0], "ro", ms = 8, label = "P(1,0)") 
ax_iq.plot([], [], ' ', label=fr"$Q_l = {Q_r:.1f}$") 
ax_iq.plot([], [], ' ', label=fr"$Q_i = {Q_i:.1f}$")         
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

#----Signal plot-----
ax_mag.plot(frequencies/1e9, signal_final, '-', lw=1)
ax_mag.set_xlabel(r"$f[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

#----Phase plot-------
ax_phase.plot(frequencies, phase_centered, '-', lw=1)
ax_phase.plot(frequencies, theta_fit, '-', lw=2, label='Arctan fit')
ax_phase.set_xlabel(r"$f [GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")
ax_phase.legend(loc ="best")

plt.show()
