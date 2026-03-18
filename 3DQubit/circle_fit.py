import numpy as np
from scipy import optimize 
from scipy.linalg import null_space
from scipy import stats

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
        r   = 0.5 *np.sqrt(B0*B0 + C0*C0 - 4.0*A0*D0) / abs(A0)
        return x_c, y_c, r

    def _fit(self, x, y):
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

    def _fit_from_complex(self, s):
        return self._fit(s.real, s.imag)


    def _guess_delay(self,f_data,z_data):
        phase2 = np.unwrap(np.angle(z_data))
        gradient, intercept, r_value, p_value, std_err = stats.linregress(f_data,phase2)
        return gradient*(-1.)/(np.pi*2.)


    def _remove_cable_delay(self,f_data,z_data, delay):
        return z_data*np.exp(+2j*np.pi*f_data*delay)

    def _fit_delay(self,f_data,z_data,delay=0.,maxiter=0):
        def residuals(p,x,y):
            phasedelay = p
            z_data_temp = y*np.exp(1j*(2.*np.pi*phasedelay*x))
            xc,yc,r0 = self._fit_from_complex(z_data_temp)
            err = np.sqrt((z_data_temp.real-xc)**2+(z_data_temp.imag-yc)**2)-r0
            return err
        p_final = optimize.leastsq(residuals,delay,args=(f_data,z_data),maxfev=10000,ftol=1e-15,xtol=1e-15)
        return p_final[0][0]


    def _canonize(self, f_data, z_data, scaling, rotation, delay):
        z_data = 1/scaling * np.exp(-1j * rotation)*self._remove_cable_delay(f_data,z_data, delay)
        return z_data
    

    def _center(self, z_data, x_c, y_c):
        z_data = z_data - (x_c + 1j *y_c)
        return z_data


    def _fit_lorentz(self, z_data, f_data):

        def lorentzian_power_tilt(f, A, f0, gamma, y0, m):

            return y0 + m*(f - f0) + A / (1 + 4*(f - f0)**2 / gamma**2)
        
        y = np.abs(z_data)
        f = f_data
        f0_guess = f[np.argmin(y)]          
        gamma_guess = (f.max() - f.min()) / 10
        A_guess = y.max() - y.min()
        y0_guess = np.median(np.r_[y[:max(10, len(y)//10)], y[-max(10, len(y)//10):]])
        m_guess  = (y[-1] - y[0]) / (f[-1] - f[0])

        p0 = [A_guess, f0_guess, gamma_guess, y0_guess, m_guess]

        popt, pcov = optimize.curve_fit(lorentzian_power_tilt, f, y, p0=p0)
        A_fit, f0_fit, gamma_fit, y0_fit, m_fit = popt

        f_and_Ql = np.array([f0_fit, f0_fit/gamma_fit])

        return f_and_Ql

    def _fit_phase (self, z_data, frequencies, theta_0_guess, Qr_guess, fr_guess):
        def theta_model(f, theta0, Qr, fr):

            return theta0 + 2*np.arctan( 2*Qr*(1.0 - f/fr) )
        
        def phase_residuals(p, f, theta):

            theta0, Qr, fr = p
            return theta_model(f, theta0, Qr, fr) - theta
        
        phase_centered = np.unwrap(np.angle(z_data))
        p0 = [theta_0_guess, Qr_guess, fr_guess] #initial guess
       

        p = optimize.least_squares(
            lambda p: phase_residuals(p, frequencies, phase_centered),
            x0=p0, bounds=([-np.pi,     0,     frequencies.min()],        
            [ np.pi, 1e7, frequencies.max()]))

        return p.x

    def _fit_notch(self, z_data, f_data, Ql_guess, Qc_guess, fr_guess, a_guess, alpha_guess, tau_guess):
        
        def S21_notch(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau):
            mod_QC = abs_Qc
            phi = phase_Qc
            return a * np.exp(1j*alpha)*np.exp(-1j* 2*np.pi*tau * f) * (1 - ((Ql/mod_QC) * np.exp(1j *phi))/(1 + 2j *Ql*(f/f0 -1)))

        def S21_notch_real(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau):
            z = S21_notch(f, Ql, abs_Qc, phase_Qc, f0, a, alpha, tau)
            return np.hstack([z.real, z.imag])

        ydata = np.hstack([z_data.real, z_data.imag])

        abs_Qc_guess = abs(Qc_guess)
        phase_Qc_guess = np.angle(Qc_guess)

        p0 = [Ql_guess , abs_Qc_guess, phase_Qc_guess, fr_guess, a_guess, alpha_guess, tau_guess]

        lower = [1,   1e1,   -np.pi, f_data.min() , 1e-2, -np.pi, -1e7]
        upper = [1e8 ,  1e8,   np.pi, f_data.max(),  1e2,  np.pi,  1e7 ]

        popt, pcov = optimize.curve_fit(S21_notch_real, f_data, ydata, p0=p0, bounds=(lower, upper), maxfev = 10000)

        return popt, pcov

