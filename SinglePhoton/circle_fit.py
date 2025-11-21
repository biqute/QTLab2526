import numpy as np
import matplotlib.pyplot as plt

# ------------------------------
# Algoritmo Chernov & Lesort
# ------------------------------

def build_matrices(x, y):
    z = x**2 + y**2
    Mzz = np.sum(z*z)
    Mxz = np.sum(x*z)
    Myz = np.sum(y*z)
    Mz  = np.sum(z)
    Mxx = np.sum(x*x)
    Mxy = np.sum(x*y)
    Myy = np.sum(y*y)
    Mx  = np.sum(x)
    My  = np.sum(y)
    n   = x.size

    M = np.array([
        [Mzz, Mxz, Myz, Mz],
        [Mxz, Mxx, Mxy, Mx],
        [Myz, Mxy, Myy, My],
        [Mz,  Mx,  My,   n ]
    ], dtype=float)

    B = np.array([
        [0., 0., 0., -2.],
        [0., 1., 0.,  0.],
        [0., 0., 1.,  0.],
        [-2.,0., 0.,  0.]
    ], dtype=float)

    return M, B


def xi_and_derivative(eta, M, B):
    A = M - eta * B
    detA = np.linalg.det(A)
    try:
        invA = np.linalg.inv(A)
        trace_term = np.trace(invA @ B)
        deriv = -detA * trace_term
    except np.linalg.LinAlgError:
        eps = 1e-6 * (1.0 + abs(eta))
        det_plus = np.linalg.det(M - (eta + eps) * B)
        deriv = (det_plus - detA) / eps
    return detA, deriv


def find_eta_star(M, B, tol=1e-12, maxiter=100):
    eta = 0.0
    for _ in range(maxiter):
        detA, deriv = xi_and_derivative(eta, M, B)
        if abs(detA) < tol:
            return eta
        if abs(deriv) < 1e-16 or np.isnan(deriv):
            eta += 1e-6
            continue
        eta_new = eta - detA / deriv
        if eta_new < 0:
            eta_new = eta / 2
        if abs(eta_new - eta) < tol:
            return eta_new
        eta = eta_new
    return eta


def nullspace_vector(A):
    U, s, Vt = np.linalg.svd(A)
    return Vt[-1, :]


def algebraic_circle_fit(x, y):
    M, B = build_matrices(x, y)
    eta_star = find_eta_star(M, B)
    A_mat = M - eta_star * B
    v = nullspace_vector(A_mat)

    denom = float(v.T @ B @ v)
    v = v / np.sqrt(abs(denom))

    Acoef, Bcoef, Ccoef, Dcoef = v

    xc = -Bcoef / (2*Acoef)
    yc = -Ccoef / (2*Acoef)
    r = np.sqrt((Bcoef*Bcoef + Ccoef*Ccoef - 4*Acoef*Dcoef) / (4*Acoef*Acoef))

    return xc, yc, r, (Acoef, Bcoef, Ccoef, Dcoef)


# ------------------------------
# Lettura CSV + Fit
# ------------------------------

def fit_from_csv(filename, plot=True):
    # CSV columns:
    # 0 = frequenza
    # 1 = Re
    # 2 = Im
    # 3 = Ampiezza
    # 4 = Fase

    data = np.genfromtxt(filename, delimiter=",", skip_header=1)
    Re = data[:, 1]
    Im = data[:, 2]

    xc, yc, r, (A,B,C,D) = algebraic_circle_fit(Re, Im)

    print("=== RISULTATI FIT CERCHIO ===")
    print(f"Centro xc = {xc}")
    print(f"Centro yc = {yc}")
    print(f"Raggio r  = {r}")
    print("\nCoefficienti algebraici:")
    print(f"A={A}, B={B}, C={C}, D={D}")

    if plot:
        theta = np.linspace(0, 2*np.pi, 200)
        xcirc = xc + r * np.cos(theta)
        ycirc = yc + r * np.sin(theta)

        plt.figure(figsize=(6,6))
        plt.plot(Re, Im, '.', label="Dati")
        plt.plot(xcirc, ycirc, '-', label="Cerchio fit")
        plt.gca().set_aspect('equal')
        plt.grid()
        plt.legend()
        plt.title("Algebraic Circle Fit (Chernov & Lesort)")
        plt.show()

    return xc, yc, r


# ------------------------------
# Esempio di utilizzo
# ------------------------------

if __name__ == "__main__":
    fit_from_csv("/Users/angelobassi/Desktop/QTLab2526/S21_data_50medie_hunger_corretto") 



