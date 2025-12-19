#!/usr/bin/env python3
import os
import ctypes
import numpy as np
import matplotlib.pyplot as plt
import time

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok, adc2mV

# ============================================================
# PARAMETRI DC
# ============================================================
TARGET_VOLTAGE_V_START = -1.310      # In Volt
TARGET_VOLTAGE_V_END = -1.4        # In Volt
VOLTAGE_STEP = -0.001               # Passo in Volt
WAVEFORM_SAMPLES = 10000           # Buffer AWG
CAPTURE_SAMPLES = 2000             # Campioni acquisizione
TIMEBASE = 5000                     # Timebase
# ============================================================

def main():
    chandle = ctypes.c_int16()
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]

    # Apertura PicoScope
    status = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)
    try:
        assert_pico_ok(status)
    except:
        ps.ps5000aChangePowerSource(chandle, status)

    print(f"PicoScope aperto (handle {chandle.value})")

    try:
        vdc_values = np.arange(TARGET_VOLTAGE_V_START, TARGET_VOLTAGE_V_END - 0.001, VOLTAGE_STEP)
        mean_values = []
        std_values = []

        for VDC in vdc_values:
            print(f"\nGenerazione segnale per VDC = {VDC:.3f} V")

            # ----------------------------------------------------
            # Configurazione AWG per DC (buffer piatto)
            # ----------------------------------------------------
            waveform = np.zeros(WAVEFORM_SAMPLES, dtype=np.int16)
            waveform_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
            offset_uV = int(VDC * 1e6)

            phase = ctypes.c_uint32()
            ps.ps5000aSigGenFrequencyToPhase(chandle, 1.0, 0, WAVEFORM_SAMPLES, ctypes.byref(phase))

            status = ps.ps5000aSetSigGenArbitrary(
                chandle,
                ctypes.c_int32(offset_uV),
                ctypes.c_uint32(0),    # pk-pk = 0
                phase, phase,
                0, 0,
                waveform_ptr,
                WAVEFORM_SAMPLES,
                0,0,0,
                0,0,
                0,0,0
            )
            assert_pico_ok(status)

            # ----------------------------------------------------
            # Configurazione Canale A
            # ----------------------------------------------------
            channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
            coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
            chARange = ps.PS5000A_RANGE["PS5000A_5V"]

            ps.ps5000aSetChannel(chandle, channelA, 1, coupling, chARange, 0)

            # ----------------------------------------------------
            # Acquisizione
            # ----------------------------------------------------
            maxADC = ctypes.c_int16()
            ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))

            timeIntervalns = ctypes.c_float()
            returnedSamples = ctypes.c_int32()
            ps.ps5000aGetTimebase2(chandle, TIMEBASE, CAPTURE_SAMPLES, ctypes.byref(timeIntervalns), ctypes.byref(returnedSamples), 0)

            ps.ps5000aRunBlock(chandle, 0, CAPTURE_SAMPLES, TIMEBASE, 0, 0, 0, None)

            ready = ctypes.c_int16(0)
            while not ready.value:
                ps.ps5000aIsReady(chandle, ctypes.byref(ready))
                time.sleep(0.01)

            bufferA = (ctypes.c_int16 * CAPTURE_SAMPLES)()
            ps.ps5000aSetDataBuffers(chandle, channelA, bufferA, None, CAPTURE_SAMPLES, 0, 0)

            overflow = ctypes.c_int16()
            cSamples = ctypes.c_int32(CAPTURE_SAMPLES)
            ps.ps5000aGetValues(chandle, 0, ctypes.byref(cSamples), 0,0,0, ctypes.byref(overflow))

            # ----------------------------------------------------
            # Analisi dati
            # ----------------------------------------------------
            data_V = np.array(adc2mV(bufferA, chARange, maxADC)) / 1000.0
            mean_v = np.mean(data_V)
            std_v = np.std(data_V)

            mean_values.append(mean_v)
            std_values.append(std_v)

            print(f"Media : {mean_v:.5f} V | Std Dev : {std_v:.5f} V")

        # ----------------------------------------------------
        # Plot con punti più piccoli
        # ----------------------------------------------------
        plt.figure(figsize=(8,4))
        plt.errorbar(
            vdc_values/2,
            mean_values,
            yerr=std_values,
            fmt='o-',       # cerchi pieni collegati da linee
            ecolor='r',
            capsize=3,
            markersize=4,
            label='Media ± std'
        )
        plt.xlabel("VDC (V)")
        plt.ylabel("VFD (V)")
        plt.title("Risposta Canale A vs VDC")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        ps.ps5000aStop(chandle)

    finally:
        ps.ps5000aCloseUnit(chandle)
        print("PicoScope chiuso.")

if __name__ == "__main__":
    main()
