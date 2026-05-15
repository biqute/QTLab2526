import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Impostazioni grafiche per mantenere la coerenza
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica",
    "axes.labelsize": 14,
    "axes.titlesize": 16,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12
})

x_min = 5
x_max = 25

def gaussian(x, amp, mean, sigma, offset):
    """Funzione Gaussiana per il fit."""
    return amp * np.exp(-(x - mean)**2 / (2 * sigma**2)) + offset

def fit_spectrum(filename, label, color_name, alpha_line, lw_line):
    try:
        data = np.loadtxt(filename)
        if(filename == "../signalGen/fft_drag.txt"):
            freq_kHz = data[:, 0] / 1000.0 - 0.6
        else:
            freq_kHz = data[:, 0] / 1000.0  # Frequenza in kHz

        amp_mV = data[:, 1]
        
        # Maschera per isolare il picco principale (evita di fittare i lobi lontani)
        mask = (freq_kHz > x_min) & (freq_kHz < x_max)
        f_fit = freq_kHz[mask]
        a_fit = amp_mV[mask]
        
        # Stima iniziale parametri: [ampiezza_max, centro, sigma_iniziale, offset_min]
        p0 = [np.max(a_fit), 15.0, 1.0, np.min(a_fit)]
        
        # Limiti per il parametro offset (modifica questi valori se vuoi un range diverso)
        offset_lower = 0
        offset_upper = 1  # Ad esempio, non più del 50% dell'ampiezza massima

        # Fit ai minimi quadrati con vincoli su offset e sigma
        popt, pcov = curve_fit(
            gaussian,
            f_fit,
            a_fit,
            p0=p0,
            bounds=([-np.inf, -np.inf, 0.0, offset_lower], [np.inf, np.inf, np.inf, offset_upper])
        )
        sigma_err = np.sqrt(np.diag(pcov))[2] # Estrazione dell'errore sulla sigma
        
        # Plot dati reali (a punti trasparenti per non appesantire il grafico)
        plt.plot(freq_kHz, amp_mV, '.', color=color_name, alpha=0.3)
        
        # Plot del fit (linea continua con le tue impostazioni)
        f_smooth = np.linspace(2.5, 27.5, 500)
        plt.plot(f_smooth, gaussian(f_smooth, *popt), color=color_name, 
                 alpha=alpha_line, linewidth=lw_line, 
                 label=f"{label} Fit: $\sigma$ = {popt[2]:.3f} kHz")
        
        return popt[1], popt[2], sigma_err # Ritorna frequenza centrale, sigma, e relativo errore
    
    except Exception as e:
        print(f"Errore caricamento o fit di {filename}: {e}")
        return None, None, None

def main():
    plt.figure(figsize=(10, 6))
    
    # Lista dei file con i tuoi parametri grafici esatti (label, color, alpha, lw)
    files = [
        ("../signalGen/fft_square.txt", "Square", "navy", 0.85, 2.0),
        ("../signalGen/fft_gauss.txt", "Gauss", "darkorange", 0.9, 2.0),
        ("../signalGen/fft_drag.txt", "DRAG", "forestgreen", 0.9, 2.0)
    ]
    
    print("\n" + "="*55)
    print(f"{'Segnale':<10} | {'Freq Centrale (kHz)':<20} | {'Sigma (kHz)':<15}")
    print("-" * 55)
    
    for path, label, color, alpha, lw in files:
        f0, sigma, err = fit_spectrum(path, label, color, alpha, lw)
        if f0 is not None:
            # Stampa i risultati quantitativi a terminale
            print(f"{label:<10} | {f0:<20.3f} | {sigma:.4f} ± {err:.4f}")
    
    print("="*55 + "\n")

    # Rifiniture grafico
    plt.axvline(15, color='red', linestyle='--', linewidth=2, alpha=0.8, label="Target (15 kHz)")
    plt.xlim(2.5, 27.5) # Zoom sulla zona di interesse
    plt.xlabel(r"Frequency (kHz)")
    #plt.ylabel(r"Amplitude")
    #plt.title("Gaussian Fit degli Spettri PICO")
    plt.legend(loc="upper right", prop = {"size": 16})
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig("../signalGen/fft_gaussian_fits.pdf")
    plt.show()

if __name__ == "__main__":
    main()