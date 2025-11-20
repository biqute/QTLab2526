import numpy as np
import matplotlib.pyplot as plt

def plot_amp_vs_frequency(filename):
    # Prova prima con virgola, se fallisce usa qualunque separatore
    try:
        data = np.genfromtxt(filename, delimiter=",", skip_header=1)
        if np.isnan(data).all():
            raise ValueError
    except:
        data = np.genfromtxt(filename, skip_header=1)  # auto-separa (spazi o tab)

    freq = data[:, 0]   # frequenze
    amp = data[:, 3]  # ampiezza

    plt.figure(figsize=(8,5))
    plt.plot(freq, amp, '-', linewidth=1)
    plt.xlabel("Freq (Hz)")
    plt.ylabel("Amplitude")
    plt.title("Amp vs Frequency")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_amp_vs_frequency("/Users/angelobassi/Desktop/QTLab2526/S21_data_50medie_hunger_corretto") 