## comincio con il fittare lo spettro del PSA

import sys
sys.path.append("../classes")
from data import Data
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

input_file = "SynthData_data"
save_as = "SA_plot_synth"

d = Data()
freq, power = d.read_txt(input_file)
freq1, freq2 = np.argmax(power[:len(power)//2]), np.argmax(power[len(power)//2:]) + len(power)//2
print(f"Peak frequencies at {freq[freq1]} GHz and {freq[freq2]} GHz")

d.fast_plot(x=freq, y=power,
            Title="Synthetiser Power Spectrum Analysis",
            x_title="Frequency [GHz]",
            y_title="Power [dB]",
            label_name="Data",
            save_as=save_as)

