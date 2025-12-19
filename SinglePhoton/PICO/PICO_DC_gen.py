#!/usr/bin/env python3
import ctypes
import numpy as np
import matplotlib.pyplot as plt
import time

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok, adc2mV

# ============================================================
TARGET_VOLTAGE_V = -1.5      # Valore DC desiderato
ARB_SAMPLES = 4096           # Lunghezza buffer AWG
CAPTURE_SAMPLES = 10000      # Numero campioni acquisizione
TIMEBASE = 5000              # Timebase per acquisizione
# ============================================================

def main():
    chandle = ctypes.c_int16()
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_16BIT"]

    # --------------------------------------------------------
    # 1) Apertura PicoScope
    # --------------------------------------------------------
    status = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)
    try:
        assert_pico_ok(status)
    except:
        ps.ps5000aChangePowerSource(chandle, status)

    print(f"PicoScope aperto (handle {chandle.value})")

    try:
        # ----------------------------------------------------
        # 2) Configurazione AWG per DC (buffer piatto)
        # ----------------------------------------------------
        waveform = np.zeros(ARB_SAMPLES, dtype=np.int16)
        waveform_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
        offset_uV = int(TARGET_VOLTAGE_V * 1e6)

        phase = ctypes.c_uint32()
        ps.ps5000aSigGenFrequencyToPhase(
            chandle,
            1.0, 0, ARB_SAMPLES,
            ctypes.byref(phase)
        )

        status = ps.ps5000aSetSigGenArbitrary(
            chandle,
            ctypes.c_int32(offset_uV),
            ctypes.c_uint32(0),      # pk-pk = 0
            phase, phase,
            0, 0,
            waveform_ptr,
            ARB_SAMPLES,
            0,0,0,
            0,0,
            0,0,0
        )
        assert_pico_ok(status)
        print(f"AWG DC impostata a {TARGET_VOLTAGE_V:.3f} V")

        # ----------------------------------------------------
        # 3) Configurazione canale A (DC, range adeguato)
        # ----------------------------------------------------
        channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
        chARange = ps.PS5000A_RANGE["PS5000A_5V"]  # range sufficiente per leggere AWG

        ps.ps5000aSetChannel(
            chandle,
            channelA,
            1, coupling, chARange, 0
        )

        # ----------------------------------------------------
        # 4) Acquisizione
        # ----------------------------------------------------
        maxADC = ctypes.c_int16()
        ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))

        timeIntervalns = ctypes.c_float()
        returnedSamples = ctypes.c_int32()
        ps.ps5000aGetTimebase2(
            chandle, TIMEBASE, CAPTURE_SAMPLES,
            ctypes.byref(timeIntervalns),
            ctypes.byref(returnedSamples), 0
        )

        print(f"dt = {timeIntervalns.value/1e6:.3f} ms | "
              f"Durata = {(timeIntervalns.value*CAPTURE_SAMPLES)/1e9:.3f} s")

        input("\nPremi INVIO per acquisire...")

        ps.ps5000aRunBlock(
            chandle, 0, CAPTURE_SAMPLES, TIMEBASE,
            0, 0, 0, None
        )

        ready = ctypes.c_int16(0)
        while not ready.value:
            ps.ps5000aIsReady(chandle, ctypes.byref(ready))
            time.sleep(0.01)

        bufferA = (ctypes.c_int16 * CAPTURE_SAMPLES)()
        ps.ps5000aSetDataBuffers(
            chandle, channelA, bufferA, None, CAPTURE_SAMPLES, 0, 0
        )

        overflow = ctypes.c_int16()
        cSamples = ctypes.c_int32(CAPTURE_SAMPLES)
        ps.ps5000aGetValues(
            chandle, 0, ctypes.byref(cSamples), 0,0,0, ctypes.byref(overflow)
        )

        # ----------------------------------------------------
        # 5) Analisi dati e plot
        # ----------------------------------------------------
        data_V = np.array(adc2mV(bufferA, chARange, maxADC)) / 1000.0

        mean_v = np.mean(data_V)
        min_v = np.min(data_V)
        max_v = np.max(data_V)

        print("\n===== RISULTATI =====")
        print(f"Media : {mean_v:.5f} V")
        print(f"Min   : {min_v:.5f} V")
        print(f"Max   : {max_v:.5f} V")

        t = np.arange(cSamples.value) * timeIntervalns.value * 1e-6

        plt.figure(figsize=(8,4))
        plt.plot(t, data_V, label="CH A")
        plt.axhline(TARGET_VOLTAGE_V, color="r", linestyle="--", label="Target DC")
        plt.xlabel("Tempo (ms)")
        plt.ylabel("Tensione (V)")
        plt.title("Generazione DC con AWG e acquisizione CH A")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        ps.ps5000aStop(chandle)

    finally:
        ps.ps5000aCloseUnit(chandle)
        print("PicoScope chiuso")

# ============================================================

if __name__ == "__main__":
    main()
