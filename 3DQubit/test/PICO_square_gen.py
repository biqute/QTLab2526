#!/usr/bin/env python3
import os
import ctypes
import numpy as np
import matplotlib.pyplot as plt

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok, adc2mV, mV2adc

# ============================================================
# 1) Caricamento DLL
# ============================================================
import os
import sys

# Trova la cartella dove si trova lo script attuale (3DQubit/test)
script_dir = os.path.abspath(os.path.dirname(__file__))

# Sale di un livello e punta alla cartella delle librerie (3DQubit/lib)
lib_path = os.path.abspath(os.path.join(script_dir, "..", "lib"))

if os.path.exists(lib_path):
    # Aggiunge il percorso a Windows e a Python (per versioni >= 3.8)
    os.environ['PATH'] = lib_path + os.path.pathsep + os.environ['PATH']
    if sys.version_info >= (3, 8):
        os.add_dll_directory(lib_path)
    print("DLL loaded from custom library path:", lib_path)
else:
    print(f"ATTENZIONE: La cartella {lib_path} non esiste!")
    # Fallback sulla cartella dello script se non trova 'lib'
    if sys.version_info >= (3, 8):
        os.add_dll_directory(script_dir)
    print("DLL fallback path:", script_dir)

# --- PARAMETRI OTTIMIZZATI PER CENTRAMENTO ---
FREQUENCY_HZ     = 500.0        # Periodo totale = 2000 us (evita ripetizioni nel grafico)
LIMIT_GAUSS      = 15.0         # Rende l'impulso stretto (6/30 del buffer = 400 us)
AMPLITUDE_VPP_V  = 1.0          
OFFSET_V         = 0.0          
WAVEFORM_SAMPLES = 30000        

def generate_square_modulated_sinusoid(samples, n_cycles, limit=3.5):
    """Genera sinusoide centrata con durata equivalente a 6-sigma."""
    t_rel = np.linspace(-limit, limit, samples)
    # L'inviluppo "accende" la sinusoide solo tra -3.0 e 3.0 (6 sigma)
    envelope = np.where(np.abs(t_rel) <= 3.0, 1.0, 0.0)
    
    t = np.linspace(0, 1, samples)
    carrier = np.sin(2 * np.pi * n_cycles * t)
    return envelope * carrier

def main():
    status = {}
    chandle = ctypes.c_int16()
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]
    status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)

    try:
        assert_pico_ok(status["openunit"])
        
        # --- Setup AWG ---
        min_val, max_val = ctypes.c_int16(), ctypes.c_int16()
        ps.ps5000aSigGenArbitraryMinMaxValues(chandle, ctypes.byref(min_val), ctypes.byref(max_val), None, None)

        f_real = 15e3  # Portante a 15 kHz 
        N_OSCILLAZIONI = f_real / FREQUENCY_HZ

        signal_float = generate_square_modulated_sinusoid(WAVEFORM_SAMPLES, N_OSCILLAZIONI, LIMIT_GAUSS)
        waveform = (signal_float * max_val.value).astype(np.int16)
        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        # Calcolo fase e invio all'AWG
        phase = ctypes.c_uint32()
        ps.ps5000aSigGenFrequencyToPhase(chandle, FREQUENCY_HZ, 0, WAVEFORM_SAMPLES, ctypes.byref(phase))

        status["setSigGenArb"] = ps.ps5000aSetSigGenArbitrary(
            chandle, int(OFFSET_V * 1e6), int(AMPLITUDE_VPP_V * 1e6),
            phase, phase, 0, 0, awg_buffer_ptr, WAVEFORM_SAMPLES,
            0, 0, 0, 0, 0, 0, 0, 0
        )
        assert_pico_ok(status["setSigGenArb"])

        # --- Setup Canale A e Trigger ---
        chRange = ps.PS5000A_RANGE["PS5000A_2V"] # Range più stretto per risoluzione
        ps.ps5000aSetChannel(chandle, 0, 1, 1, chRange, 0)
        
        maxADC = ctypes.c_int16()
        ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
        
        # Trigger al passaggio per lo zero (Rising edge a 100mV per stabilità)
        threshold_adc = int(mV2adc(100, chRange, maxADC))
        ps.ps5000aSetSimpleTrigger(chandle, 1, 0, threshold_adc, 2, 0, 1000)

       # --- Sezione 5) Acquisizione per centrare a 400us ---
        timebase = 80 
        
        # Vogliamo che il trigger (inizio impulso) sia a 200us
        preTriggerSamples = 200   # 200 us prima del trigger (circa)
        postTriggerSamples = 600  # 600 us dopo il trigger (circa)
        totalSamples = preTriggerSamples + postTriggerSamples
        
        # 1. Chiedi al PicoScope il VERO intervallo di tempo (dt) per timebase=80
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        ps.ps5000aGetTimebase2(chandle, timebase, totalSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
        
        # 2. Calcola il dt in microsecondi
        dt_us = timeIntervalns.value / 1000.0

        status["runBlock"] = ps.ps5000aRunBlock(
            chandle, preTriggerSamples, postTriggerSamples, 
            timebase, None, 0, None, None
        )
        
        ready = ctypes.c_int16(0)
        while ready.value == 0: ps.ps5000aIsReady(chandle, ctypes.byref(ready))

        buffer = (ctypes.c_int16 * totalSamples)()
        ps.ps5000aSetDataBuffers(chandle, 0, ctypes.byref(buffer), None, totalSamples, 0, 0)
        ps.ps5000aGetValues(chandle, 0, ctypes.byref(ctypes.c_int32(totalSamples)), 0, 0, 0, None)

        # --- Plot ---
        data_mV = adc2mV(buffer, chRange, maxADC)
        
        # 3. Costruisci l'asse dei tempi usando il dt reale
        # Se vuoi che il tempo t=0 corrisponda all'evento di trigger:
        time_axis = (np.arange(totalSamples) - preTriggerSamples) * dt_us
        
        data_to_save = np.column_stack((time_axis, data_mV))
        filename_txt = "../signalGen/square_env_data.txt"
        np.savetxt(filename_txt, data_to_save, fmt='%.6f', header="Time(us) Voltage(mV)", delimiter='\t')
        print(f"Dati salvati in: {filename_txt}")

        plt.figure(figsize=(10, 5))
        plt.plot(time_axis, data_mV)
        plt.title(f"Square signal - {f_real/1000} kHz")
        plt.xlabel("Time (µs)")
        plt.ylabel("Voltage (mV)")
        plt.grid(True)
        # 1. Generiamo i tick da 200 a 600 con passo 50
        # Nota: mettiamo 601 perché l'estremo destro in range() è escluso
        ticks_personalizzati = list(range(200, 401, 20))

        # 2. Applichiamo i tick all'asse x
        plt.xticks(ticks_personalizzati)       
        
        nome_grafico = "square_env_plot.pdf"
        plt.savefig(f"../signalGen/{nome_grafico}")
        print(f"Grafico salvato in: ../signalGen/{nome_grafico}")
        plt.show()
        
        

    finally:
        ps.ps5000aCloseUnit(chandle)

if __name__ == "__main__":
    main()