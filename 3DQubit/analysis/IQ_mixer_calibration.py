import numpy as np
from scipy import optimize
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import sys
sys.path.append("../")
from circle_fit import CircleFitter

def fit_ellipse(z_data, theta_data,  I_0_guess, A_I_guess, Q_0_guess, A_Q_guess, Dtheta_guess):
        
        def IQ_resp(theta, I_0, A_I, Q_0, A_Q, Dtheta):
            return Q_0 + A_Q*np.cos(theta + Dtheta) + 1j *(I_0 + A_I*np.cos(theta))

        def IQ_real(theta, I_0, A_I, Q_0, A_Q, Dtheta):
            z = IQ_resp(theta, I_0, A_I, Q_0, A_Q, Dtheta)
            return np.hstack([z.real, z.imag])

        ydata = np.hstack([z_data.real, z_data.imag])

        p0 = [ I_0_guess, A_I_guess, Q_0_guess, A_Q_guess, Dtheta_guess]

        lower = [-1e3, -1e3,-1e3, -1e3, -np.pi]
        upper = [1e3 , 1e3, 1e3,  1e3,  np.pi]

        popt, pcov = optimize.curve_fit(IQ_real, theta_data, ydata, p0=p0, bounds=(lower, upper), maxfev = 10000)

        return popt, pcov



########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})


################ MAIN ########################
# ---------------- Load data ----------------
data = np.loadtxt("../data/acquisizione.txt")
time = data[:, 0] #ns
I = data[:, 1] #mV
Q = data[:, 2] #mV
theta = np.unwrap(np.arctan2(I, Q))

#-------Mixer Response----

R = Q + 1j*I

fitter = CircleFitter()

x_c, y_c, r_0 = fitter._fit_from_complex(R)

theta = np.linspace(0, 2*np.pi, 400)
xcirc = r_0 * np.cos(theta) +x_c
ycirc = r_0 * np.sin(theta) +y_c
#----Mixer fit--


params, pcov = fit_ellipse(R, theta, I_0_guess=0, A_I_guess=100, Q_0_guess=0, A_Q_guess=100, Dtheta_guess=np.pi/2)

theta_x = np.linspace(-np.pi, np.pi, 2000)

fitted_R = params[2] + params[3]*np.cos(theta_x + params[4]) + 1j*(params[0] + params[1]*np.cos(theta_x))

print ("Fitted parameters:", params, "\nCovariance matrix:", pcov)
# === Plot ===

fig, ax = plt.subplots()

#----Signal plot-----
ax.plot(Q, I, marker='o', linestyle='', markeredgecolor='blue', markerfacecolor='white', ms=8,  label="Mixer Response")
ax.plot(xcirc, ycirc,'-', ms=1.5, color = "red", label="Fitted Response")
ax.plot(x_c, y_c,marker='o', ms=1.5, color = "red", label="x_c, y_c")
ax.set_xlabel(r"$Q$")
ax.set_ylabel(r"$I$")
ax.axis('equal')
ax.legend()
#ax_mag.grid(True, alpha=0.3)
ax.set_title("Mixer Response")

plt.show()

