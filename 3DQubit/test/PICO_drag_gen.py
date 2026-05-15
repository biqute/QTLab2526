#!/usr/bin/env python3
import os
import sys
import ctypes
import numpy as np
import matplotlib.pyplot as plt

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok, adc2mV, mV2adc

# ============================================================
# 1) Caricamento DLL
# ============================================================
script_dir = os.path.abspath(os.path.dirname(__file__))
lib_path = os.path.abspath(os.path.join(script_dir, "..", "lib"))

if os.path.exists(lib_path):
    os.environ['PATH'] = lib_path + os.path.pathsep + os.environ['PATH']
    if sys.version_info >= (3, 8):
        os.add_dll_directory(lib_path)
    print("DLL loaded from custom library path:", lib_path)
else:
    print(f"ATTENZIONE: La cartella {lib_path} non esiste!")
    if sys.version_info >= (3, 8):
        os.add_dll_directory(script_dir)
    print("DLL fallback path:", script_dir)

# ================== PARAMETRI AWG ===========================
FREQUENCY_HZ      = 1500.0       # Frequenza di ripetizione dell'intero buffer (Hz)
AMPLITUDE_VPP_V   = 1.0          # Volt picco-picco
OFFSET_V          = 0.0          # Offset (V)
WAVEFORM_SAMPLES  = 30000        # Punti tabella AWG

def generate_drag_pulse(samples, n_cycles, limit=3.0, beta=0.5):
    """
    Genera un impulso DRAG (Gaussiana + Derivata in quadratura) modulato su una portante.
    """
    t_rel = np.linspace(-limit, limit, samples)
    I_env = np.exp(-0.5 * t_rel**2)
    Q_env = -beta * t_rel * I_env
    
    t_carrier = np.linspace(0, 1, samples)
    carrier_I = np.cos(2 * np.pi * n_cycles * t_carrier)
    carrier_Q = np.sin(2 * np.pi * n_cycles * t_carrier)
    
    signal = I_env * carrier_I + Q_env * carrier_Q
    
    max_amp = np.max(np.abs(signal))
    if max_amp > 0:
        signal = signal / max_amp
        
    return signal

# ============================================================

def main():
    status = {}
    chandle = ctypes.c_int16()
   
    # --------------------------------------------------------
    # 2) Apri PicoScope in modalità 16-BIT
    # --------------------------------------------------------
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]
    status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)

    try:
        assert_pico_ok(status["openunit"])
    except:
        powerStatus = status["openunit"]
        if powerStatus in (286, 282):
            status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
            assert_pico_ok(status["changePowerSource"])
        else:
            raise

    print(f"PicoScope aperto (16-bit), handle = {chandle.value}")

    try:
        # ----------------------------------------------------
        # 3) Setup AWG (Generatore di Funzioni)
        # ----------------------------------------------------
        min_val, max_val = ctypes.c_int16(), ctypes.c_int16()
        
        status["arbMinMax"] = ps.ps5000aSigGenArbitraryMinMaxValues(
            chandle, ctypes.byref(min_val), ctypes.byref(max_val), None, None
        )
        assert_pico_ok(status["arbMinMax"])

        # Parametri Impulso
        f_real = 15e3  # Portante a 15 kHz 
        N_OSCILLAZIONI = f_real / FREQUENCY_HZ
        BETA_DRAG = 0.5 
        LIMIT_SIGMA = 3.0

        signal_float = generate_drag_pulse(WAVEFORM_SAMPLES, N_OSCILLAZIONI, LIMIT_SIGMA, BETA_DRAG)
        waveform = (signal_float * max_val.value).astype(np.int16)
        
        print("\n=== INFO AWG (DRAG) ===")
        print(f"Frequenza Portante Target: {f_real} Hz")
        print(f"Frequenza Ripetizione Buffer: {FREQUENCY_HZ} Hz")
        print(f"Punti buffer: {WAVEFORM_SAMPLES}")

        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        # Calcolo fase
        phase = ctypes.c_uint32()
        status["freqToPhase"] = ps.ps5000aSigGenFrequencyToPhase(
            chandle, ctypes.c_double(FREQUENCY_HZ), 0,
            ctypes.c_uint32(WAVEFORM_SAMPLES), ctypes.byref(phase)
        )
        assert_pico_ok(status["freqToPhase"])

        # Impostazione AWG
        status["setSigGenArb"] = ps.ps5000aSetSigGenArbitrary(
            chandle,
            ctypes.c_int32(int(OFFSET_V * 1e6)),
            ctypes.c_uint32(int(AMPLITUDE_VPP_V * 1e6)),
            phase, phase,
            0, 0,
            awg_buffer_ptr,
            ctypes.c_int32(WAVEFORM_SAMPLES),
            0, 0, 0, 0, 0, 0, 0, 0
        )
        assert_pico_ok(status["setSigGenArb"])
       
        print("AWG Avviato. Premi INVIO per acquisire...")
        input()

        # ----------------------------------------------------
        # 4) Configurazione Canale A e Trigger
        # ----------------------------------------------------
        channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
        chRange = ps.PS5000A_RANGE["PS5000A_5V"]

        status["setChA"] = ps.ps5000aSetChannel(chandle, channelA, 1, coupling, chRange, 0)
        assert_pico_ok(status["setChA"])

        maxADC = ctypes.c_int16()
        ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))

        # Trigger falling edge a -200mV
        threshold_adc = int(mV2adc(-200, chRange, maxADC))
        direction = 3 # PS5000A_FALLING
       
        status["trigger"] = ps.ps5000aSetSimpleTrigger(
            chandle, 1, channelA, threshold_adc, direction, 0, 1000
        )
        assert_pico_ok(status["trigger"])

        # ----------------------------------------------------
        # 5) Timebase e Acquisizione
        # ----------------------------------------------------
        preTriggerSamples = 400
        postTriggerSamples = 400 
        timebase = 64
        totalSamples = preTriggerSamples + postTriggerSamples
       
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        status["getTimebase"] = ps.ps5000aGetTimebase2(
            chandle, timebase, totalSamples,
            ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0
        )
        assert_pico_ok(status["getTimebase"])
        
        dt_us = timeIntervalns.value / 1000.0 # Conversione immediata del dt in microsecondi
        print(f"Timebase: {timebase} (dt = {dt_us} µs)")
        print(f"Durata acquisizione: {dt_us * totalSamples / 1000.0:.2f} ms")

        status["runBlock"] = ps.ps5000aRunBlock(
            chandle, preTriggerSamples, postTriggerSamples,
            timebase, None, 0, None, None
        )
        assert_pico_ok(status["runBlock"])

        ready = ctypes.c_int16(0)
        while ready.value == 0:
            status["isReady"] = ps.ps5000aIsReady(chandle, ctypes.byref(ready))

        # Recupero Dati
        bufferMax = (ctypes.c_int16 * totalSamples)()
       
        status["setDataBuffers"] = ps.ps5000aSetDataBuffers(
            chandle, channelA, ctypes.byref(bufferMax), None, totalSamples, 0, 0
        )
        assert_pico_ok(status["setDataBuffers"])

        cmaxSamples = ctypes.c_int32(totalSamples)
        overflow = ctypes.c_int16()
       
        status["getValues"] = ps.ps5000aGetValues(
            chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow)
        )
        assert_pico_ok(status["getValues"])
        
        # ----------------------------------------------------
        # 6) Plot
        # ----------------------------------------------------
        data_mV = adc2mV(bufferMax, chRange, maxADC)
        
        # COSTRUZIONE ASSE TEMPI CORRETTA (Zero centrato sul trigger)
        time_axis_us = (np.arange(cmaxSamples.value) - preTriggerSamples) * dt_us
        
        # Salvataggio dati
        data_to_save = np.column_stack((time_axis_us, data_mV))
        
        # Assicurati che la cartella esista prima di salvare
        os.makedirs("../signalGen", exist_ok=True)
        filename_txt = "../signalGen/drag_env_data.txt"
        np.savetxt(filename_txt, data_to_save, fmt='%.6f', header="Time(us)\tVoltage(mV)", delimiter='\t')
        print(f"Dati salvati in: {filename_txt}")
        
        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(time_axis_us, data_mV) 
        plt.xlabel("Time (µs)")
        plt.ylabel("Voltage (mV)")
        plt.title(f"PICO DRAG Pulse - Carrier: {f_real/1000} kHz")
        plt.grid(True)
        
        nome_grafico = "drag_env_plot.pdf"
        plt.savefig(f"../signalGen/{nome_grafico}")
        print(f"Grafico salvato in: ../signalGen/{nome_grafico}")
        
        plt.show()

        status["stop"] = ps.ps5000aStop(chandle)

    except Exception as e:
        print(f"ERRORE: {str(e)}")
    finally:
        status["close"] = ps.ps5000aCloseUnit(chandle)
        print("PicoScope chiuso.")

if __name__ == "__main__":
    main()