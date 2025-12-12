#!/usr/bin/env python3
import os
import ctypes
import numpy as np
import matplotlib.pyplot as plt
import time

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok, adc2mV, mV2adc

# ============================================================
# SETUP LIBRERIE
# ============================================================
dll_path = os.path.abspath(os.path.dirname(__file__))
os.add_dll_directory(dll_path)

# ================== PARAMETRI DC ============================
TARGET_VOLTAGE_V = 0        # Tensione DC desiderata (-500 mV)
WAVEFORM_SAMPLES = 4096        # Dimensione buffer (arbitraria per DC)
# ============================================================

def main():
    status = {}
    chandle = ctypes.c_int16()
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]

    # 1) Apertura PicoScope
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

    print(f"PicoScope aperto, handle = {chandle.value}")

    try:
        # ----------------------------------------------------
        # 2) Configurazione AWG per DC
        # ----------------------------------------------------
        # Per fare DC con la modalità Arbitrary, creiamo un buffer "piatto"
        # (pieno di zeri) e impostiamo l'ampiezza (pk-pk) a 0.
        # L'uscita sarà determinata solo dall'OFFSET.
        
        waveform = np.zeros(WAVEFORM_SAMPLES, dtype=np.int16)
        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        # Parametri API
        offset_uV = int(TARGET_VOLTAGE_V * 1e6) # -500000 uV
        pk_to_pk_uV = 0                         # 0 uV (Nessuna oscillazione)
        
        # Frequenza fittizia (necessaria per l'API, ma ininfluente per DC pura)
        phase = ctypes.c_uint32(0) 
        # Calcoliamo phase per 1 Hz giusto per riempire i campi
        ps.ps5000aSigGenFrequencyToPhase(chandle, 1.0, 0, WAVEFORM_SAMPLES, ctypes.byref(phase))

        status["setSigGenArb"] = ps.ps5000aSetSigGenArbitrary(
            chandle,
            ctypes.c_int32(offset_uV),            # offset = -0.5 V
            ctypes.c_uint32(pk_to_pk_uV),         # pkToPk = 0 V
            phase,                                # startDeltaPhase
            phase,                                # stopDeltaPhase
            ctypes.c_uint32(0),                   # deltaPhaseIncrement
            ctypes.c_uint32(0),                   # dwellCount
            awg_buffer_ptr,                       # buffer
            ctypes.c_int32(WAVEFORM_SAMPLES),     # size
            0,                                    # sweepType (UP)
            0,                                    # operation (OFF)
            0,                                    # indexMode (SINGLE)
            0,                                    # shots (infinito)
            0,                                    # sweeps (infinito)
            0,                                    # triggerType (RISING)
            0,                                    # triggerSource (NONE)
            0,                                    # extInThreshold
        )
        assert_pico_ok(status["setSigGenArb"])
        
        print(f"\nAWG Configurato: Output DC fisso a {TARGET_VOLTAGE_V} V")
        
        # ----------------------------------------------------
        # 3) Configurazione Canale A per leggere il segnale
        # ----------------------------------------------------
        channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
        
        # Range +/- 1V è ideale per leggere -0.5V con buona risoluzione
        chARange = ps.PS5000A_RANGE["PS5000A_1V"]

        status["setChA"] = ps.ps5000aSetChannel(
            chandle, channelA, 1, coupling, chARange, 0
        )
        assert_pico_ok(status["setChA"])

        # Disabilita gli altri canali
        for ch_name in ["PS5000A_CHANNEL_B", "PS5000A_CHANNEL_C", "PS5000A_CHANNEL_D"]:
            ps.ps5000aSetChannel(chandle, ps.PS5000A_CHANNEL[ch_name], 0, coupling, chARange, 0)

        # ----------------------------------------------------
        # 4) ACQUISIZIONE (NO TRIGGER!)
        # ----------------------------------------------------
        # IMPORTANTE: Non chiamiamo ps5000aSetSimpleTrigger.
        # Vogliamo acquisire subito, indipendentemente dal segnale (DC = linea piatta).
        
        maxADC = ctypes.c_int16()
        ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))

        # Timebase: Rallentiamo un po' per vedere una linea stabile nel tempo
        # Timebase 5000 -> circa 40 microsecondi per sample (su serie 5000)
        # Total time = 2000 samples * 40us = 80ms
        timebase = 5000 
        maxSamples = 2000
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        ps.ps5000aGetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
        print(f"Timebase: {timebase}, dt: {timeIntervalns.value/1e6:.3f} ms, Durata totale: {(timeIntervalns.value * maxSamples)/1e9:.3f} s")

        input("\nPremi INVIO per acquisire il segnale DC...")

        status["runBlock"] = ps.ps5000aRunBlock(
            chandle,
            0,              # preTrigger
            maxSamples,     # postTrigger
            timebase,
            0,              # oversample
            0,           # timeIndisposedMs
            0,              # segmentIndex
            None,           # lpReady
        )
        assert_pico_ok(status["runBlock"])

        # Attesa fine acquisizione
        ready = ctypes.c_int16(0)
        while ready.value == 0:
            ps.ps5000aIsReady(chandle, ctypes.byref(ready))
            time.sleep(0.01)

        # Recupero dati
        bufferAMax = (ctypes.c_int16 * maxSamples)()
        bufferAMin = (ctypes.c_int16 * maxSamples)() # Non usato in 8-bit mode solitamente
        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(maxSamples)

        ps.ps5000aSetDataBuffers(chandle, channelA, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples, 0, 0)
        ps.ps5000aGetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))

        # ----------------------------------------------------
        # 5) Plot
        # ----------------------------------------------------
        data_mV = adc2mV(bufferAMax, chARange, maxADC)
        data_V = np.array(data_mV) / 1000.0
        time_axis = np.linspace(0, (cmaxSamples.value -1) * timeIntervalns.value, cmaxSamples.value)

        mean_val = np.mean(data_V)
        print(f"\nMedia letta: {mean_val:.4f} V")
        print(f"Target     : {TARGET_VOLTAGE_V:.4f} V")

        plt.figure()
        plt.plot(time_axis * 1e-6, data_V, label="Canale A") # Tempo in ms
        plt.axhline(y=TARGET_VOLTAGE_V, color='r', linestyle='--', label="Target DC")
        plt.ylim(TARGET_VOLTAGE_V - 0.2, TARGET_VOLTAGE_V + 0.2) # Zoom verticale
        plt.xlabel("Tempo (ms)")
        plt.ylabel("Tensione (V)")
        plt.title("Generazione DC con AWG")
        plt.legend()
        plt.grid(True)
        plt.show()

        ps.ps5000aStop(chandle)

    finally:
        ps.ps5000aCloseUnit(chandle)
        print("PicoScope chiuso.")

if __name__ == "__main__":
    main()