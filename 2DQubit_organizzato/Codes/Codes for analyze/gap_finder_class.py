from typing import List
import numpy as np
from scipy.constants import k, hbar
from scipy.special import kv, iv
from iminuit import cost, Minuit
from matplotlib import pyplot as plt
import matplotlib

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
        omega = 7492528819.8433*2*np.pi, #from our data
        inv_q_0 = 3.933612733477039e-06 , #from our data 
        alpha = 0.73394, # found from Sonnet simulation
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

    def chi2(self):
        if self.fit_result is None:
            print("No fit found: doing it now")
            _ = self.fit()
        return self.fit_result.fval / (len(self._temps) - self.fit_result.npar)

    # Basic plot of the data
    def plot(self):
        plt.scatter(self._temps, self._q_inv, s = 0.8)
        plt.show()

    # Fit with chosen model and plot result
    def plot_fit(self):
        plt.figure(dpi = 120)
        plt.errorbar(self._temps, self._q_inv, self._err_q_inv, marker='.', linestyle='None')
        if self.fit_result is None:
            print("No fit found: doing it now")
            _ = self.fit()

        chi = str(round(self.chi2(), 2))
        delta0 = str(round(self.fit_result.values[0] * 6.242e-2, 5)) + " meV"
        textstr = '\n'.join((r'$\tilde{\chi}^2 = $' + chi, r'$\Delta = $'+delta0))
        props = dict(boxstyle = 'round', facecolor = 'white', alpha = 0.9)
        plt.text(50, 6e-4, textstr, fontsize = 14, verticalalignment = 'top',  bbox = props)
        x_axis = np.linspace(self._temps[self.mask][0], self._temps[self.mask][-1]+10, 100)
        plt.plot(x_axis, self._fit_function(x_axis, *self.fit_result.values), color = 'red', label = 'fit')

        plt.legend(loc = 'upper center', bbox_to_anchor = (0.5, 1.2))
        plt.grid()
        plt.show()
    
    # Nice plot comparing Kondo and standard fit methods
    def plot_fit_compare(self):
        fig = plt.figure(dpi = 150)
        ax = fig.add_subplot(111)
        ax.errorbar(self._temps, self._q_inv, self._err_q_inv, linestyle = ' ', marker = 'o', markersize = 3, label = "Data")

        self.set_fit_type('standard')
        _ = self.fit()
        ax.plot(self._temps[self.mask], self._fit_function(self._temps[self.mask], *self.fit_result.values), 
             color = 'red', linestyle = '--', label = 'Standard fit')
        plt.ylim([self._fit_function(self._temps[self.mask][0], *self.fit_result.values)*0.95, 
                 self._fit_function(self._temps[self.mask], *self.fit_result.values)[-1]])

        self.set_fit_type('kondo')
        _ = self.fit()
        ax.plot(self._temps[self.mask], self._fit_function(self._temps[self.mask], *self.fit_result.values), 
             color = 'red', label = 'Kondo fit')

        plt.xlim([self._temps[self.mask][0], self._temps[self.mask][-1]+10])
        lgd = plt.legend(loc = 'upper center', bbox_to_anchor = (0.5, 1.2), ncol = 3, columnspacing = 0.8)
        plt.grid()
        ax.ticklabel_format(style = 'sci', axis = 'y', scilimits = (0, 0))
        t = ax.yaxis.get_offset_text()
        t.set_x(-0.1)
        plt.xlabel("T (mK)")
        plt.ylabel(r"$1/Q_i$")
       # plt.savefig("Kondo_fit.pdf", bbox_extra_artists = (lgd, ), bbox_inches = 'tight')
        plt.show()
