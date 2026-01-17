import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec 

########## SCRIPT 4 LATEX #####
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

def choose_cable()

def attenuation_func(x, p):
    return p[0] * np.exp(-p[1] * x) + p[2]*np.sin(p[3]*x+p[4]) + p[5]