import math
import numpy as np
import matplotlib.pyplot as plt
from iminuit import Minuit
from iminuit.cost import LeastSquares

# This makes your plot look like latex. Great for writing papers!
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

def Q_fit(x, Q_0, ):
    return  offset + A/ ((x-w_0)^2+L^2)



fig, ax = plt.subplots()
ax.set_xlabel(r"$f$(GHz)")
ax.set_ylabel(r"$S11$ Power in dB)")
ax.plot(x_values,y_values)
plt.show()  