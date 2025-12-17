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
TARGET_VOLTAGE_V_START = -900.0  # Partiamo da -900 mV
TARGET_VOLTAGE_V_END = -1700.0   # Fino a -1700 mV
VOLTAGE_STEP = -20.0             # Passo di 20 mV
WAVEFORM_SAMPLES = 10000         # Dimensione buffer
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
        # Prepara i dati per il grafico
        vdc_values = np.arange(TARGET_VOLTAGE_V_START, TARGET_VOLTAGE_V_END - 1, VOLTAGE_STEP)
        vfd_values = []

        for VDC in vdc_values:
            print(f"Generando segnale per VDC = {VDC} mV")
            # ----------------------------------------------------
            # 2) Configurazione AWG per DC
            # ----------------------------------------------------
            # Genera la tensione DC
            waveform = np.zeros(WAVEFORM_SAMPLES, dtype=np.int16)
            awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))


            phase = ctypes.c_uint32(0)
            ps.ps5000aSigGenFrequencyToPhase(chandle, 1.0, 0, WAVEFORM_SAMPLES, ctypes.byref(phase))

            status["setSigGenArb"] = ps.ps5000aSetSigGenArbitrary(
                chandle,
                0,  # offset
                0,  # pkToPk
                phase,  # startDeltaPhase
                phase,  # stopDeltaPhase
                ctypes.c_uint32(0),  # deltaPhaseIncrement
                ctypes.c_uint32(0),  # dwellCount
                awg_buffer_ptr,  # buffer
                ctypes.c_int32(WAVEFORM_SAMPLES),  # size
                0,  # sweepType
                0,  # operation
                0,  # indexMode
                0,  # shots
                0,  # sweeps
                0,  # triggerType
                0,  # triggerSource
                0,  # extInThreshold
            )
            assert_pico_ok(status["setSigGenArb"])

            # ----------------------------------------------------
            # 3) Configurazione Canale A per leggere il segnale
            # ----------------------------------------------------
            channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
            coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
            chARange = ps.PS5000A_RANGE["PS5000A_1V"]  # Range più sensibile per VFD

            status["setChA"] = ps.ps5000aSetChannel(
                chandle, channelA, 1, coupling, chARange, 0
            )
            assert_pico_ok(status["setChA"])

            # ----------------------------------------------------
            # 4) ACQUISIZIONE (NO TRIGGER!)
            # ----------------------------------------------------
            maxADC = ctypes.c_int16()
            ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))

            timebase = 5000
            maxSamples = 2000
            timeIntervalns = ctypes.c_float()
            returnedMaxSamples = ctypes.c_int32()

            ps.ps5000aGetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)

            # Acquisizione
            status["runBlock"] = ps.ps5000aRunBlock(
                chandle,
                0,              # preTrigger
                maxSamples,     # postTrigger
                timebase,
                0,              # oversample
                0,              # timeIndisposedMs
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
            bufferAMin = (ctypes.c_int16 * maxSamples)()
            overflow = ctypes.c_int16()
            cmaxSamples = ctypes.c_int32(maxSamples)

            ps.ps5000aSetDataBuffers(chandle, channelA, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples, 0, 0)
            ps.ps5000aGetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))

            # ----------------------------------------------------
            # 5) Calcolo dei valori VFD
            # ----------------------------------------------------
            data_mV = adc2mV(bufferAMax, chARange, maxADC)
            vfd_values.append(data_mV[0])  # Usa il primo valore di VFD per ogni VDC

            print(f"VDC: {VDC} mV, VFD: {data_mV[0]:.4f} mV")  # Stampa VFD per il valore corrente di VDC

        # ----------------------------------------------------
        # 6) Plot senza errore standard
        # ----------------------------------------------------
        plt.plot(vdc_values, vfd_values, 'o-', label="VFD")
        plt.xlabel("VDC (mV)")
        plt.ylabel("VFD (mV)")
        plt.title("VFD vs VDC")
        plt.legend()
        plt.grid(True)
        plt.show()

        ps.ps5000aStop(chandle)

    finally:
        ps.ps5000aCloseUnit(chandle)
        print("PicoScope chiuso.")

if __name__ == "__main__":
    main()
