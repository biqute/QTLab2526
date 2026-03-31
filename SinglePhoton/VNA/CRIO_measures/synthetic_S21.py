import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json

def generate_synthetic_s21(freqs, params):
    """
    Generates clean synthetic S21 data for a notch-type resonator based on the Probst model.
    """
    # Extract parameters from the dictionary
    fr = params["fr"]
    Qc_mag = params["Qc_mag"]
    Qi = params["Qi"]
    phi = params["phi"]
    tau = params["tau"]
    a = params["a"]
    alpha = params["alpha"]

    # Compute Q_l and complex Q_c
    Qc_complex = Qc_mag * np.exp(-1j * phi)
    Ql = 1.0 / (1 / Qc_mag + 1 / Qi)

    # Calculate theoretical S21
    x = (freqs - fr) / fr
    denom = 1 + 2j * Ql * x
    coupling_factor = Ql / Qc_complex

    S21_clean = a * np.exp(1j * alpha) * (1 - coupling_factor / denom)
    
    # Apply cable delay
    S21_clean *= np.exp(-2j * np.pi * freqs * tau)  

    return S21_clean

def add_noise(S21_clean, SNR_dB):
    """
    Injects complex Gaussian noise into the signal based on the specified SNR.
    """
    signal_power = np.mean(np.abs(S21_clean)**2)
    noise_power = signal_power / (10**(SNR_dB / 10))
    sigma = np.sqrt(noise_power / 2)
    
    noise = sigma * (np.random.randn(len(S21_clean)) + 1j * np.random.randn(len(S21_clean)))
    return S21_clean + noise

def save_dataset(freqs, S21, params, filename="synthetic_s21"):
    """
    Saves the noisy S21 data to a CSV and the ground truth parameters to a JSON file.
    """
    # Save the data array to CSV
    df = pd.DataFrame({
        "frequency": freqs,
        "Re(S21)": S21.real,
        "Im(S21)": S21.imag,
        "amplitude": np.abs(S21),
        "phase": np.angle(S21)
    })
    csv_name = f"{filename}.csv"
    df.to_csv(csv_name, index=False)
    print(f"Data successfully saved to {csv_name}")

    # Save the ground truth metadata to JSON
    json_name = f"{filename}_meta.json"
    with open(json_name, "w") as f:
        json.dump(params, f, indent=4)
    print(f"Ground truth parameters saved to {json_name}")

def plot_resonance(freqs, S21_noisy, S21_clean=None):
    """
    Visualizes the S21 data in the complex plane, alongside magnitude and phase plots.
    """
    fig = plt.figure(figsize=(12, 8))

    # IQ Circle Plot (Left side, takes up two rows)
    ax1 = plt.subplot(2, 2, (1, 3))
    if S21_clean is not None:
        ax1.plot(S21_clean.real, S21_clean.imag, '-', label='Clean Theory', alpha=0.7, color='orange')
    ax1.plot(S21_noisy.real, S21_noisy.imag, '.', ms=2, label='Noisy Data', color='blue')
    ax1.set_title("Notch-Type S21 (Complex Plane)")
    ax1.set_xlabel("Re(S21)")
    ax1.set_ylabel("Im(S21)")
    ax1.grid(True)
    ax1.axis('equal')
    ax1.legend()

    # Magnitude Plot (Top right)
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(freqs, 20 * np.log10(np.abs(S21_noisy)), '.', ms=2, color='blue')
    ax2.set_title("Magnitude vs Frequency")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("|S21| (dB)")
    ax2.grid(True)

    # Phase Plot (Bottom right)
    ax3 = plt.subplot(2, 2, 4)
    ax3.plot(freqs, np.angle(S21_noisy), '.', ms=2, color='blue')
    ax3.set_title("Phase vs Frequency")
    ax3.set_xlabel("Frequency (Hz)")
    ax3.set_ylabel("arg(S21) (rad)")
    ax3.grid(True)

    plt.tight_layout()
    plt.show()

# -------------------------------------------------------
# Execution Block
# -------------------------------------------------------
if __name__ == "__main__":
    
    # 1. Define Ground Truth Parameters
    ground_truth_params = {
        "Qc_mag": 1e3,
        "Qi": 1e4,
        "fr": 5e9,
        "phi": 0.1 * np.pi,
        "tau": 50e-9,        # Corrected to 50 ns
        "a": 0.2,
        "alpha": 0.2 * np.pi,
        "SNR_dB": 40
    }

    # 2. Setup Frequency Sweep
    N = 2001
    freqs_delay = np.linspace(4.950e9, 5.14e9, N)

    # 3. Execute Pipeline
    S21_clean = generate_synthetic_s21(freqs_delay, ground_truth_params)
    S21_noisy = add_noise(S21_clean, ground_truth_params["SNR_dB"])
    
    # 4. Save and Visualize
    save_dataset(freqs_delay, S21_noisy, ground_truth_params)
    plot_resonance(freqs_delay, S21_noisy, S21_clean)