import numpy as np
import matplotlib.pyplot as plt
from iminuit import cost, Minuit
from scipy.constants import k, hbar
from scipy.special import kv, iv

class GapFinder():
    """
    Class implementing the fit procedure of quality factor values extracted 
    from resonance data to obtain the energy gap of a superconductor.
    Current main functionalities:
        plotting
        fitting
    """
    def __init__(
        self, 
        filename, 
        omega = 3.03*1e9, 
        inv_q_0 = 4.791014e-5, 
        alpha = 0.86766, # found from Sonnet simulation
        fit_type = "standard"
    ):
        self.fit_result = None

        self.omega = omega
        self.inv_q_0 = inv_q_0
        self.alpha = alpha
        self.set_fit_type(fit_type)
        self._readfile(filename)

    def set_fit_type(self, fit_type):
        self.fit_type = fit_type
        ourk = 1.380649
        if fit_type == 'kondo':        
            def model(val_t, delta0, Tk, b, q0):
                val_t = val_t * 1e-3
                xi = hbar * self.omega / (2 * k * val_t)
                sigma1 = 4*np.exp(-delta0/(ourk*val_t))*np.sinh(xi)*kv(0, xi)
                sigma2 = np.pi*(1-2*np.exp(-delta0/(ourk*val_t))*np.exp(-xi)*iv(0, xi))
                
                return -b*np.log(val_t*1e3/Tk) + 1*self.alpha*sigma1/sigma2 + q0
            
        if fit_type == 'standard':        
            def model(val_t, delta0, q0):
                val_t = val_t * 1e-3
                xi = hbar * self.omega / (2 * k * val_t)
                sigma1 = 4*np.exp(-delta0/(ourk*val_t))*np.sinh(xi)*kv(0, xi)
                sigma2 = np.pi*(1-2*np.exp(-delta0/(ourk*val_t))*np.exp(-xi)*iv(0, xi))
                
                return self.alpha*sigma1/sigma2 + q0
            
        self._fit_function = model
    
    def set_T_limit(self, max):
        self.mask = self._temps<max

    def _readfile(self, filename):
        temps = []
        q_inv = []
        err_q_inv = []

        with open(filename, encoding = 'utf-8') as file:
            for line in file:
                splitted = [float(x) for x in line.split(' ')]
                temps.append(splitted[0])
                q_inv.append(splitted[1])
                err_q_inv.append(splitted[2])

        self._temps = np.array(temps, dtype = 'float64')
        self._q_inv = np.array(q_inv, dtype = 'float64')
        self._err_q_inv = np.array(err_q_inv, dtype = 'float64')
        self.inv_q_0 = self._q_inv[0]

    def fit(self, init_parameters = None):
        if init_parameters is None:
            
            if self.fit_type == 'standard':
                init_parameters = [2, self.inv_q_0]
                
            if self.fit_type == 'kondo':
                init_parameters = [2, 40, 1e-4, self.inv_q_0]
                
        cost_func = cost.LeastSquares(self._temps[self.mask], self._q_inv[self.mask], 
                                      self._err_q_inv[self.mask], self._fit_function)
        m_obj = Minuit(cost_func, *init_parameters)
        m_obj.limits['delta0'] = (0, None)
        m_obj.limits['q0'] = (self.inv_q_0*0.95, self.inv_q_0*1.05)
        #m_obj.fixed['q0'] = True
        
        if self.fit_type == 'kondo':
            m_obj.limits['delta0'] = (0, None)
            m_obj.limits['Tk'] = (0, None)
            m_obj.limits['b'] = (0, None)

        self.fit_result = m_obj
        m_obj.migrad(ncall = 10000, iterate = 20)
        return m_obj