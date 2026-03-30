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
dll_path = os.path.abspath(os.path.dirname(__file__))
os.add_dll_directory(dll_path)
print("DLL loaded from:", dll_path)

# ================== PARAMETRI AWG ===========================
FREQUENCY_HZ      = 8200.0       # 1.5 kHz (Periodo ~666 µs)   #8200Hz
DUTY_CYCLE_TARGET = 0.9991       # 99.98 %                     #99.91%  
AMPLITUDE_VPP_V   = 1.43         # Volt picco-picco            #1.44  
# Offset per avere segnale tra 0V (High) e -1.39V (Low)
OFFSET_V          = -AMPLITUDE_VPP_V / 2
WAVEFORM_SAMPLES  = 31000         # punti tabella AWG
# ============================================================

# Funzione per calcolare la FWHM (larghezza a metà altezza) per un picco in discesa
def calculate_fwhm(time_axis, data_mV):
    # Trova il minimo del segnale (picco in giù)
    min_value = np.min(data_mV)
    half_max = min_value + (0 - min_value) / 2.0  # Mezzo dell'intervallo dal minimo a 0V

    # Trova i punti in cui il segnale è uguale a metà della profondità del picco
    below_half_max = np.where(data_mV <= half_max)[0]

    # Calcolare la larghezza a metà altezza
    fwhm_start = time_axis[below_half_max[0]]
    fwhm_end = time_axis[below_half_max[-1]]

    fwhm = fwhm_end - fwhm_start
    return fwhm

def main():
    status = {}
    chandle = ctypes.c_int16()
   
    # --------------------------------------------------------
    # 2) Apri PicoScope in modalità 16-BIT
    # --------------------------------------------------------
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]
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
        min_val = ctypes.c_int16()
        max_val = ctypes.c_int16()
        min_size = ctypes.c_uint32()
        max_size = ctypes.c_uint32()

        # Ottieni i limiti del buffer AWG
        try:
            status["arbMinMax"] = ps.ps5000aSigGenArbitraryMinMaxValues(
                chandle, ctypes.byref(min_val), ctypes.byref(max_val),
                ctypes.byref(min_size), ctypes.byref(max_size)
            )
            assert_pico_ok(status["arbMinMax"])
        except AttributeError:
            # Fallback se la funzione non esiste nella lib in uso
            min_val.value, max_val.value = -32768, 32767
            min_size.value, max_size.value = 1, 49152

        # Calcolo buffer AWG
        high_samples = int(round(WAVEFORM_SAMPLES * DUTY_CYCLE_TARGET))
        low_samples = WAVEFORM_SAMPLES - high_samples
        waveform = np.empty(WAVEFORM_SAMPLES, dtype=np.int16)
        waveform[:high_samples] = max_val.value # HIGH
        waveform[high_samples:] = min_val.value # LOW

        actual_duty = np.count_nonzero(waveform == max_val.value) / WAVEFORM_SAMPLES
       
        print("\n=== INFO AWG ===")
        print(f"Frequenza Target: {FREQUENCY_HZ} Hz")
        print(f"Duty Cycle: {actual_duty*100:.4f}%")
        print(f"Configurazione Tensione: Max ~0V, Min ~{OFFSET_V - AMPLITUDE_VPP_V/2:.2f}V")

        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        # Calcolo fase
        phase = ctypes.c_uint32()
        status["freqToPhase"] = ps.ps5000aSigGenFrequencyToPhase(
            chandle, ctypes.c_double(FREQUENCY_HZ), 0,
            ctypes.c_uint32(WAVEFORM_SAMPLES), ctypes.byref(phase)
        )
        assert_pico_ok(status["freqToPhase"])

        # Impostazione AWG
        offset_uV = int(OFFSET_V * 1e6)
        pk_to_pk_uV = int(AMPLITUDE_VPP_V * 1e6)
       
        status["setSigGenArb"] = ps.ps5000aSetSigGenArbitrary(
            chandle,
            ctypes.c_int32(offset_uV),
            ctypes.c_uint32(pk_to_pk_uV),
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

        # Ottieni valore ADC max per le conversioni
        maxADC = ctypes.c_int16()
        ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))

        # TRIGGER MODIFICATO: Falling edge, soglia negativa (-200mV)
        threshold_adc = int(mV2adc(-200, chRange, maxADC))
        direction = 3 # PS5000A_FALLING
       
        status["trigger"] = ps.ps5000aSetSimpleTrigger(
            chandle, 1, channelA, threshold_adc, direction, 0, 1000
        )
        assert_pico_ok(status["trigger"])

        # ----------------------------------------------------
        # 5) Timebase e Acquisizione
        # ----------------------------------------------------
        timebase = 2
        preTriggerSamples = 10
        postTriggerSamples = 50
        totalSamples = preTriggerSamples + postTriggerSamples
       
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        status["getTimebase"] = ps.ps5000aGetTimebase2(
            chandle, timebase, totalSamples,
            ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0
        )
        assert_pico_ok(status["getTimebase"])
        print(f"Timebase: {timebase} (dt = {timeIntervalns.value} ns)")

        status["runBlock"] = ps.ps5000aRunBlock(
            chandle, preTriggerSamples, postTriggerSamples,
            timebase, None, 0, None, None
        )
        assert_pico_ok(status["runBlock"])

        # Attesa fine acquisizione
        ready = ctypes.c_int16(0)
        while ready.value == 0:
            status["isReady"] = ps.ps5000aIsReady(chandle, ctypes.byref(ready))

        # Recupero Dati
        bufferMax = (ctypes.c_int16 * totalSamples)()
        bufferMin = (ctypes.c_int16 * totalSamples)() # Non usato in questo modo, ma richiesto
       
        status["setDataBuffers"] = ps.ps5000aSetDataBuffers(
            chandle, channelA, ctypes.byref(bufferMax), ctypes.byref(bufferMin),
            totalSamples, 0, 0
        )
        assert_pico_ok(status["setDataBuffers"])

        cmaxSamples = ctypes.c_int32(totalSamples)
        overflow = ctypes.c_int16()
       
        status["getValues"] = ps.ps5000aGetValues(
            chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow)
        )
        assert_pico_ok(status["getValues"])

        # ----------------------------------------------------
        # 6) Calcolo FWHM
        # ----------------------------------------------------
        data_mV = adc2mV(bufferMax, chRange, maxADC)
        time_axis = np.linspace(
            0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value
        )

        fwhm = calculate_fwhm(time_axis, data_mV)
        print(f"Larghezza a metà altezza (FWHM): {fwhm:.4f} ns")

        # ----------------------------------------------------
        # 7) Plot
        # ----------------------------------------------------
        plt.figure(figsize=(12, 6))
        plt.plot(time_axis / 1000.0, data_mV)  # x in µs
        plt.xlabel("Tempo (µs)")
        plt.ylabel("Tensione (mV)")
        plt.title(f"Acquisizione AWG (16-bit) - {FREQUENCY_HZ} Hz")
        plt.grid(True)
        
        plt.tight_layout()
        
        plt.show()

        status["stop"] = ps.ps5000aStop(chandle)

    except Exception as e:
        print(f"ERRORE: {str(e)}")
    finally:
        status["close"] = ps.ps5000aCloseUnit(chandle)
        print("PicoScope chiuso.")

if __name__ == "__main__":
    main()
