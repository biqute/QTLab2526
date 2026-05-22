import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import re

files = sorted(glob.glob("Data/*.txt"))

powers = []
S21_list = []
freq_axis = None

for file in files:

    # --- extract power from filename ---
    name = os.path.basename(file)
    match = re.search(r"(-?\d+)", name)
    if match:
        P = float(match.group(1))
    else:
        continue

    data = np.loadtxt(file)

    freq = data[:, 0]
    re_s21 = data[:, 1]
    im_s21 = data[:, 2]

    s21 = re_s21 + 1j * im_s21

    # store
    if freq_axis is None:
        freq_axis = freq

    powers.append(P)
    S21_list.append(s21)

# --- convert to arrays ---
powers = np.array(powers)
S21_list = np.array(S21_list)

# sort by power
idx = np.argsort(powers)
powers = powers[idx]
S21_list = S21_list[idx, :]

# --- choose what to plot ---
S21_mag_db = np.abs(S21_list)

# meshgrid
FREQ, PWR = np.meshgrid(freq_axis / 1e9, powers)

# --- plot ---
plt.figure(figsize=(9,6))

pcm = plt.pcolormesh(
    FREQ,
    PWR,
    S21_mag_db,
    shading="auto"
)

plt.xlabel("Frequency (GHz)")
plt.ylabel("Power (dBm)")
plt.title("Punchout Map")

cbar = plt.colorbar(pcm)
cbar.set_label("|S21|")

plt.tight_layout()
plt.show()