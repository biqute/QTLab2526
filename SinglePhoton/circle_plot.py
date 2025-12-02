import numpy as np
import matplotlib.pyplot as plt

def plot_circle(filename):
    # Leggi file CSV (prova prima con virgola)
    try:
        data = np.genfromtxt(filename, delimiter=",", skip_header=1)
        if np.isnan(data).all():
            raise ValueError
    except:
        data = np.genfromtxt(filename, skip_header=1)

    Re = data[:, 1]
    Im = data[:, 2]

    plt.figure(figsize=(6,6))
    plt.plot(Re, Im, '.', markersize=3)
    plt.xlabel("Re[S21]")
    plt.ylabel("Im[S21]")
    plt.title("Resonator Circle in the Complex Plane")
    plt.grid(True)
    plt.axis("equal")  
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_circle(r"C:\Users\kid\labQT\Lab2025\Single photon\QTLab2526\SinglePhoton\S21_hanger100medie_corretto_peak2") 
