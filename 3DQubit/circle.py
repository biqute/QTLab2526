import numpy as np
from scipy import optimize
from scipy.linalg import null_space
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

def char_eq(M, B, eta):
    return np.linalg.det(M - eta * B)

data = np.load("data.npz")

frequencies = data['0']['freq']
signal = np.abs(data['0']['signal'])
phase = np.unwrap(data['0']['phase'])
  

#print("min =", np.min(phase), "max =", np.max(phase)) used to check if deg or rad

real_S21 = signal * np.cos(phase)
imag_S21 = signal * np.sin(phase)

x, y = real_S21, imag_S21
z = x*x + y*y  # z = x^2 + y^2
n = x.size

#-----Computing Momenta---------
Sx   = np.sum(x)
Sy   = np.sum(y)
Sz   = np.sum(z)
Sxx  = np.sum(x*x)
Syy  = np.sum(y*y)
Szz  = np.sum(z*z)
Sxy  = np.sum(x*y)
Sxz  = np.sum(x*z)
Syz  = np.sum(y*z)

# --- Moment matrix M ---
M = np.array([
    [Szz, Sxz, Syz, Sz],
    [Sxz, Sxx, Sxy, Sx],
    [Syz, Sxy, Syy, Sy],
    [Sz,  Sx,  Sy,  n ]
], dtype=float)

# --- Constraint matrix B ---
B = np.array([
    [0.0, 0.0, 0.0, -2.0],
    [0.0, 1.0, 0.0,  0.0],
    [0.0, 0.0, 1.0,  0.0],
    [-2.0,0.0, 0.0,  0.0]
], dtype=float)

#--Solving Mx = eta Bx using Newton's method---
f = lambda eta: char_eq(M, B, eta)

eta0 = optimize.newton(f, 0) #initial guess for eta*
print("Found smallest eigenvalue:", eta0)

#--Finding corresponding eigenvector--
D = M - eta0 * B
A = null_space(D)         #Returns the whole eigenspace of eta0
a = A[:, 0]               #By construction there is only one, safety check passed
a = a  

alpha = a @ B @ a

if alpha ==0 :
    raise ZeroDivisionError(" A^T B A = 0 -> Can't normalize")

a /= np.sqrt(alpha) # normalize it respct to B

# ---- Extract circle parameters ----

A0, B0, C0, D0 = a
if A0 == 0:
    raise ZeroDivisionError("A = 0 -> r_0 can't be computed")

x_c = -0.5 * B0 / A0
y_c = -0.5 * C0 / A0
r_0 = 0.5 * 1/abs(A0)


# ---- Plot ----
theta = np.linspace(0, 2*np.pi, 400)
xcirc = x_c + r_0 * np.cos(theta)
ycirc = y_c + r_0 * np.sin(theta)

# --Layout: big left (IQ), right (mag, phase) ---
fig = plt.figure(figsize=(10, 6), constrained_layout=True)

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
ax_iq.plot(real_S21, imag_S21, '.', ms=1.5, label='Data')
ax_iq.plot(xcirc, ycirc, '-', lw=2, label='Fitted circle')
ax_iq.set_aspect('equal', 'box')
ax_iq.set_xlabel(r"$\Re\{S_{21}\}$")          
ax_iq.set_ylabel(r"$\Im\{S_{21}\}$")          
ax_iq.legend(loc='best')
ax_iq.set_title(r"I-Q Plot")

ax_mag.plot(frequencies/1e9, signal, '-', lw=1)
ax_mag.set_xlabel(r"$f[GHz]$")
ax_mag.set_ylabel(r"$|S_{21}|$")
ax_mag.grid(True, alpha=0.3)
ax_mag.set_title("Magnitude")

ax_phase.plot(frequencies/1e9, phase, '-', lw=1)
ax_phase.set_xlabel(r"$f [GHz]$")
ax_phase.set_ylabel(r"$\phi [rad]$")
ax_phase.grid(True, alpha=0.3)
ax_phase.set_title("Phase")

plt.show()
