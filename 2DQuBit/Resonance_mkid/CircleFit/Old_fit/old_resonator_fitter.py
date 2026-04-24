import numpy as np
from scipy import optimize, stats
from scipy.linalg import null_space

class CircleEstimator:
    """
    Algebraic circle fitting via a generalized eigenvalue approach.
    """

    def __init__(self):
        self.params = None
        self.coefficients = None
        self.eta_value = None

    # Calcola la somma dei momenti dai dati reali (x) e immaginari (y) 

    @staticmethod
    def _compute_moments(x, y):
        z = x**2 + y**2
        return {
            "sum_x": np.sum(x),
            "sum_y": np.sum(y),
            "sum_z": np.sum(z),
            "sum_xx": np.sum(x*x),
            "sum_yy": np.sum(y*y),
            "sum_zz": np.sum(z*z),
            "sum_xy": np.sum(x*y),
            "sum_xz": np.sum(x*z),
            "sum_yz": np.sum(y*z),
            "n_points": x.size
        }

    # Costruisce la matrice M dei momenti e la matrice di vincolo B

    @staticmethod
    def _construct_matrices(m):
        M_matrix = np.array([
            [m["sum_zz"], m["sum_xz"], m["sum_yz"], m["sum_z"]],
            [m["sum_xz"], m["sum_xx"], m["sum_xy"], m["sum_x"]],
            [m["sum_yz"], m["sum_xy"], m["sum_yy"], m["sum_y"]],
            [m["sum_z"],  m["sum_x"],  m["sum_y"],  m["n_points"]]
        ], dtype=float)

        B_matrix = np.array([
            [0., 0., 0., -2.],
            [0., 1., 0., 0.],
            [0., 0., 1., 0.],
            [-2., 0., 0., 0.]
        ], dtype=float)

        return M_matrix, B_matrix
    
    # Calcola il determinante di (M -eta B)

    @staticmethod
    def _determinant_function(M, B, eta):
        return np.linalg.det(M - eta * B)

    # Tramite algoritmo di Newton trova l'autovalore eta

    @staticmethod
    def _find_eta(M, B):
        func = lambda e: CircleEstimator._determinant_function(M, B, e)
        return optimize.newton(func, 0.0)

    # Impone a^(T)Ba=1 per soddisfare il vincolo imposto

    @staticmethod
    def _normalize_vector(vec, B):
        norm_factor = vec @ B @ vec
        if np.isclose(norm_factor, 0.0):
            raise ZeroDivisionError("Cannot normalize: a^T B a = 0")
        return vec / np.sqrt(norm_factor)

    #  Determina il centro della circonferenza e il raggio

    @staticmethod
    def _circle_params(A, B, C, D):
        if np.isclose(A, 0.0):
            raise ZeroDivisionError("Cannot compute radius: A=0")
        x_center = -0.5 * B / A
        y_center = -0.5 * C / A
        radius = 0.5 * np.sqrt(B**2 + C**2 - 4*A*D) / abs(A)
        return x_center, y_center, radius
    
    # Unisce tutto il procedimento per il fit algebrico del cerchio tramite le funzioni definite sopra

    def fit(self, x, y):
        moments = self._compute_moments(x, y)
        M, B = self._construct_matrices(moments)
        eta_val = self._find_eta(M, B)
        self.eta_value = eta_val

        D_matrix = M - eta_val * B
        null_vecs = null_space(D_matrix)
        if null_vecs.size == 0:
            raise RuntimeError("Null space is empty; no solution found")

        vec = self._normalize_vector(null_vecs[:, 0], B)
        self.coefficients = vec
        A, Bc, Cc, Dc = vec

        self.params = self._circle_params(A, Bc, Cc, Dc)
        return self.params
    

    def fit_from_complex(self, z):
        return self.fit(z.real, z.imag)
    
    # Utilizza una regressione lineare per stimare tau: slope = -2*pi*tau
    def estimate_delay(self, freq, z):
        phases = np.unwrap(np.angle(z))
        slope, _, _, _, _ = stats.linregress(freq, phases)
        return -slope / (2 * np.pi)
    
    # Rimozione del delay

    def remove_delay(self, freq, z, delay):
        return z * np.exp(2j * np.pi * freq * delay)
    
    # Affina il delay con un fit ai minimi quadrati tramite leastsq

    def fit_with_delay(self, freq, z, initial_delay=0.0, max_iter=0):
        def residual(p, f, z_data):
            delay = p
            z_adj = z_data * np.exp(2j * np.pi * delay * f)
            xc, yc, r = self.fit_from_complex(z_adj)
            return np.sqrt((z_adj.real - xc)**2 + (z_adj.imag - yc)**2) - r

        result = optimize.leastsq(
            residual, initial_delay, args=(freq, z), maxfev=10000, ftol=1e-15, xtol=1e-15
        )
        return result[0][0]
    
    # Sposta il cerchio a (1,0)

    def canonize_data(self, freq, z, scale, rotation, delay):
        return 1/scale * np.exp(-1j * rotation) * self.remove_delay(freq, z, delay)
