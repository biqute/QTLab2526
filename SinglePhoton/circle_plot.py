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

    #mask = (data[:, 0] <= 8.6455e9) & (data[:, 0] >= 8.6422e9) #5.976e9 e 5.995e9 PICCO1 #7.489e9 e 7.4935e9 PICCO2 #7.8091e9 7.8127e9 PICCO3 #7.99e9 7.9935e9 PICCO4 #8.233e9 8.255e9 PICCO5 #8.6422e9 8.6455e9 PICCO6
   # data = data[mask]
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
    plot_circle(r"C:\Users\kid\labQT\Lab2025\Single photon\QTLab2526\SinglePhoton\VNA\CRIO_measures_new\300mk\picco1_big_new300mk.csv") 
