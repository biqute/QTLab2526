import numpy as np
from scipy import optimize
from scipy.linalg import null_space

class CircleFitter:
    """
    Algebraic circle fit using generalized eigenvalue problem.
    """

    def __init__(self):
        self.params_ = None
        self.coeffs_ = None
        self.eta_ = None

    @staticmethod
    def _moments(x, y):
        z = x*x + y*y
        return {
            "Sx":   np.sum(x),
            "Sy":   np.sum(y),
            "Sz":   np.sum(z),
            "Sxx":  np.sum(x*x),
            "Syy":  np.sum(y*y),
            "Szz":  np.sum(z*z),
            "Sxy":  np.sum(x*y),
            "Sxz":  np.sum(x*z),
            "Syz":  np.sum(y*z),
            "n":    x.size
        }

    @staticmethod
    def _build_matrices(m):
        M = np.array([
            [m["Szz"], m["Sxz"], m["Syz"], m["Sz"]],
            [m["Sxz"], m["Sxx"], m["Sxy"], m["Sx"]],
            [m["Syz"], m["Sxy"], m["Syy"], m["Sy"]],
            [m["Sz"],  m["Sx"],  m["Sy"],  m["n" ]]
        ], dtype=float)

        B = np.array([
            [0.0, 0.0, 0.0, -2.0],
            [0.0, 1.0, 0.0,  0.0],
            [0.0, 0.0, 1.0,  0.0],
            [-2.0,0.0, 0.0,  0.0]
        ], dtype=float)

        return M, B

    @staticmethod
    def _char_eq(M, B, eta):
        return np.linalg.det(M - eta * B)

    @staticmethod
    def _solve_eta(M, B):
        f = lambda e: CircleFitter._char_eq(M, B, e)
        return optimize.newton(f, 0.0)

    @staticmethod
    def _normalize_eigenvector(a, B):
        alpha = a @ B @ a
        if np.isclose(alpha, 0.0):
            raise ZeroDivisionError("a^T B a = 0 → can't normalize")
        return a / np.sqrt(alpha)

    @staticmethod
    def _coeffs_to_params(A0, B0, C0, D0):
        if np.isclose(A0, 0.0):
            raise ZeroDivisionError("A0 = 0 → r can't be computed")
        x_c = -0.5 * B0 / A0
        y_c = -0.5 * C0 / A0
        r   = 0.5 / abs(A0)
        return x_c, y_c, r

    def fit(self, x, y):
        m = self._moments(x, y)
        M, B = self._build_matrices(m)
        eta = self._solve_eta(M, B)
        self.eta_ = eta

        D = M - eta * B
        A = null_space(D)
        if A.size == 0:
            raise RuntimeError("Null space empty; no eigenvector")

        a = A[:, 0]
        a = self._normalize_eigenvector(a, B)
        self.coeffs_ = a
        A0, B0, C0, D0 = a

        x_c, y_c, r = self._coeffs_to_params(A0, B0, C0, D0)
        self.params_ = (x_c, y_c, r)
        return self.params_

    def fit_from_complex(self, s):
        return self.fit(s.real, s.imag)

    def residuals_tau(self, freqs: np.ndarray, S_raw: np.ndarray, tau_guess: float) -> np.ndarray:
        """
        Return residual vector r_i = [(x_i-xc)^2+(y_i-yc)^2] - r^2
        to pass to LSM
        """
        # remove delay using initial tau_guess 
        S_calibrated = S_raw * np.exp(+1j * 2*np.pi * tau_guess * freqs)

        # fit circle on corrected data
        x_c, y_c, r = self.fit_from_complex(S_calibrated)

        # radial-squared per point minus r^2
        x, y = S_calibrated.real, S_calibrated.imag
        d2 = (x - x_c)**2 + (y - y_c)**2
        
        return r**2 - d2

