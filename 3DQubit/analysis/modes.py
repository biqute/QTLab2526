import sys
sys.path.append("../classes")
from data import Data
import matplotlib.pyplot as plt
import numpy as np

input_file = "resonance_circular_cav"
save_as = "residuals_plot"
d = Data()
n_modes, f_meas, f_exp = d.read_txt(input_file, spacing=";")
residuals = f_meas - f_exp
print(n_modes)
print(f_meas)
print(f_exp)
d.fast_plot(x=n_modes, y=residuals, 
                Title="Residuals Plot", 
                x_title="Number of Frequencies", 
                y_title="Residuals (GHz)",
                point_tipe = 'o',
                save_as=save_as)



