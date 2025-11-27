import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Circle fitting using the Chernov–Taubin algebraic circle fit
# (recommended by Probst et al.)
# ---------------------------------------------------------------------
def fit_circle_taubin(x, y):
    # Data centroid
    x_m = np.mean(x)
    y_m = np.mean(y)

    # Shifted coordinates
    u = x - x_m
    v = y - y_m

    # Moments
    Suu = np.sum(u**2)
    Suv = np.sum(u * v)
    Svv = np.sum(v**2)
    Suuu = np.sum(u**3)
    Suvv = np.sum(u * v**2)
    Svvv = np.sum(v**3)
    Svuu = np.sum(v * u**2)

    # Solve linear system
    A = np.array([
        [Suu, Suv],
        [Suv, Svv]
    ])

    B = 0.5 * np.array([
        [Suuu + Suvv],
        [Svvv + Svuu]
    ])

    uc, vc = np.linalg.solve(A, B)

    # Center in original coordinates
    xc = uc[0] + x_m
    yc = vc[0] + y_m

    # Radius
    r = np.sqrt(uc[0]**2 + vc[0]**2 + (Suu + Svv) / len(x))

    return xc, yc, r


# ---------------------------------------------------------------------
# Load delay-corrected data
# ---------------------------------------------------------------------
data = pd.read_csv("S21_no_delay.csv")

x = data["Re(S21)"].values
y = data["Im(S21)"].values

# ---------------------------------------------------------------------
# Perform circle fit
# ---------------------------------------------------------------------
xc, yc, r0 = fit_circle_taubin(x, y)

print("Fitted circle parameters:")
print(f"x_c = {xc}")
print(f"y_c = {yc}")
print(f"r_0 = {r0}")

# ---------------------------------------------------------------------
# Prepare circle for plotting
# ---------------------------------------------------------------------
theta = np.linspace(0, 2*np.pi, 400)
circle_x = xc + r0 * np.cos(theta)
circle_y = yc + r0 * np.sin(theta)

# Coordinates for radius line
radius_x = [xc, xc - r0]
radius_y = [yc, yc]

# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------
plt.figure(figsize=(6,6))

# Plot data and fitted circle
plt.plot(x, y, '.', ms=2, label="S21 data")
plt.plot(circle_x, circle_y, 'r-', label="Fitted circle")

# Mark center
plt.plot(xc, yc, 'ko', label="Circle center")

# Draw radius line
plt.plot(radius_x, radius_y, 'k--', label="Radius r₀")

# ---- Emphasize axes ----
plt.axhline(0, color='black', linewidth=1.2)   # Real axis (x-axis)
plt.axvline(0, color='black', linewidth=1.2)   # Imag axis (y-axis)

# Labels and cosmetics
plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.title("Algebraic Circle Fit (Chernov/Taubin)")
plt.axis("equal")
plt.grid(True)
plt.legend(loc="upper right")
plt.tight_layout()
plt.show()

#Recently fitted parameters
#x_c = -0.021780511582819996
#y_c = 0.05455076885607019
#r_0 = 0.04527254564185787
#Estimated cable delay tau = 5.0295 ns