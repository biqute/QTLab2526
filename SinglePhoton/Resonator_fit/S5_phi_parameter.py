import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# Circle fitting (Chernov–Taubin method)
# ---------------------------------------------------------
def fit_circle_taubin(x, y):
    x_m = np.mean(x)
    y_m = np.mean(y)

    u = x - x_m
    v = y - y_m

    Suu = np.sum(u**2)
    Suv = np.sum(u * v)
    Svv = np.sum(v**2)
    Suuu = np.sum(u**3)
    Suvv = np.sum(u * v**2)
    Svvv = np.sum(v**3)
    Svuu = np.sum(v * u**2)

    A = np.array([[Suu, Suv],
                  [Suv, Svv]])
    B = 0.5 * np.array([Suuu + Suvv,
                        Svvv + Svuu])

    uc, vc = np.linalg.solve(A, B)

    xc = uc + x_m
    yc = vc + y_m
    r0 = np.sqrt(uc**2 + vc**2 + (Suu + Svv) / len(x))

    return xc, yc, r0


# ---------------------------------------------------------
# Load S21 data (already delay-corrected)
# ---------------------------------------------------------
data = pd.read_csv("S21_no_delay.csv")

mask = data["frequency"] <= 5.004e9
data = data[mask]

S21 = data["Re(S21)"].values + 1j * data["Im(S21)"].values
freq = data["frequency"].values

# ---------------------------------------------------------
# Apply scaling factor a and global phase shift α
# ---------------------------------------------------------
#a = float(input("Enter scaling factor a: "))
#alpha = float(input("Enter global phase shift α (radians): "))

a = 0.1
alpha = 2.0

S21_norm = S21 / (a * np.exp(1j * alpha))

# Extract real/imag for fitting
x = S21_norm.real
y = S21_norm.imag

# ---------------------------------------------------------
# Fit normalized circle
# ---------------------------------------------------------
xc, yc, r0 = fit_circle_taubin(x, y)

print("\n===== Normalized Circle Fit Results =====")
print(f"x_c = {xc}")
print(f"y_c = {yc}")
print(f"r_0 = {r0}")

# Compute φ
phi = -np.arcsin(yc / r0)
print(f"\nEstimated φ = {phi} radians")
print(f"φ (in degrees) = {phi * 180/np.pi}°")

# ---------------------------------------------------------
# Prepare circle for plotting
# ---------------------------------------------------------
theta = np.linspace(0, 2*np.pi, 400)
circle_x = xc + r0 * np.cos(theta)
circle_y = yc + r0 * np.sin(theta)

radius_x = [xc, xc - r0]
radius_y = [yc, yc]

# ---------------------------------------------------------
# Plot normalized circle with fit
# ---------------------------------------------------------
plt.figure(figsize=(6,6))
plt.plot(x, y, '.', ms=3, label="Normalized S21 data")
plt.plot(circle_x, circle_y, 'r-', label="Fitted circle")

plt.plot(xc, yc, 'ko', label="Circle center")
plt.plot(radius_x, radius_y, 'k--', label="Radius r₀")

# emphasise axes
plt.axhline(0, color='gray', linewidth=2)
plt.axvline(0, color='gray', linewidth=2)

plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.title("Normalized S21 Circle + Fitted Circle")
plt.axis("equal")
plt.grid(True)
plt.legend(loc="upper right")
plt.tight_layout()
plt.show()
