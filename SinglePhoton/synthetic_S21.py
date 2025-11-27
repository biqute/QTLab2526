import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# -------------------------------------------------------
# Parameters (updated meaning)
# -------------------------------------------------------
Qc_mag = 1e3
Qi = 1e4
fr = 5e9                     # 5 GHz
phi = 0.0                  # phase of complex Qc 0.1 * np.pi
tau = 5e-9                  # 50 ns
a = 1.0                      # amplitude scaling
alpha = 0.0 * np.pi         # overall phase shift (global) 0.4 * np.pi 

# Frequency sweep
N = 2001
span = fr / 2000
freqs = np.linspace(fr - span, fr + span, N)

# Linear fit to determine slope of phase vs frequence requires off resonant data
#freqs_delay = np.linspace(4.993e9, 5.01e9, N)

freqs_delay = np.linspace(4.950e9, 5.14e9, N)
#freqs_delay = np.linspace(4.90e9, 5.10e9, N)

# -------------------------------------------------------
# Compute Q_l and complex Q_c*
# -------------------------------------------------------
Qc_complex = Qc_mag * np.exp(-1j * phi)
Ql = 1.0 / (1/Qc_mag + 1/Qi)

# -------------------------------------------------------
# Synthetic S21 model (Eq. 1 in Probst et al. with modifications)
# -------------------------------------------------------
def S21_model(freq):
    x = (freq - fr) / fr
    denom = 1 + 2j * Ql * x
    coupling_factor = (Ql / Qc_complex)

    S21 = a * np.exp(1j * alpha) * (1 - coupling_factor / denom)
    S21 *= np.exp(-2j * np.pi * freq * tau)  # cable delay
    return S21

S21_clean = S21_model(freqs_delay)

# -------------------------------------------------------
# Add complex Gaussian noise
# -------------------------------------------------------
SNR_dB = 40
signal_power = np.mean(np.abs(S21_clean)**2)
noise_power = signal_power / (10**(SNR_dB/10))
sigma = np.sqrt(noise_power/2)

noise = sigma * (np.random.randn(N) + 1j*np.random.randn(N))
S21_noisy = S21_clean + noise

# -------------------------------------------------------
# Save data to CSV
# -------------------------------------------------------
df = pd.DataFrame({
    "frequency": freqs_delay,
    "Re(S21)": S21_noisy.real,
    "Im(S21)": S21_noisy.imag,
    "amplitude": np.abs(S21_noisy),
    "phase": np.angle(S21_noisy)
})

df.to_csv("synthetic_s21.csv", index=False)
print("Saved synthetic data to synthetic_s21.csv")

# -------------------------------------------------------
# Plots
# -------------------------------------------------------
plt.figure(figsize=(6,6))
plt.plot(S21_noisy.real, S21_noisy.imag, '.', ms=2, label='Noisy')
#plt.plot(S21_clean.real, S21_clean.imag, '-', label='Clean')
plt.title("Synthetic Notch-Type S21 (Complex Plane)")
plt.xlabel("Re(S21)")
plt.ylabel("Im(S21)")
plt.grid(True)
plt.axis('equal')
plt.legend()
plt.show()

plt.figure(figsize=(8,4))
plt.subplot(1,2,1)
plt.plot(freqs_delay, 20*np.log10(np.abs(S21_noisy)), '.', ms=2)
plt.title("Magnitude vs Frequency")
plt.xlabel("Frequency (Hz)")
plt.ylabel("|S21| (dB)")
plt.grid(True)

plt.subplot(1,2,2)
plt.plot(freqs_delay, np.angle(S21_noisy), '.', ms=2)
plt.title("Phase vs Frequency")
plt.xlabel("Frequency (Hz)")
plt.ylabel("arg(S21) (rad)")
plt.grid(True)

plt.tight_layout()
plt.show()



#PARAMETERS USED TO ILLUSTRATE BEST DOMAIN FOR CABLE FIT (ASYMMETRY CAUSED BY PHI)
#Qc_mag = 1e3
#Qi = 1e4
#fr = 5e9                     # 5 GHz
#phi = 0.1 * np.pi           # phase of complex Qc
#tau = 5e-9                  # 50 ns
#a = 0.1                      # amplitude scaling
#alpha = 0.4 * np.pi          # overall phase shift (global)

#freqs_delay = np.linspace(4.80e9, 5.20e9, N)