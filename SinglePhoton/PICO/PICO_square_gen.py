#!/usr/bin/env python3
import os
import ctypes
import numpy as np
import matplotlib.pyplot as plt

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import assert_pico_ok, adc2mV, mV2adc

# ============================================================
# 1) Rende visibili le DLL nella cartella corrente
#    (stesso trucco che usi in test_pico.py)
# ============================================================
dll_path = os.path.abspath(os.path.dirname(__file__))
os.add_dll_directory(dll_path)
print("DLL loaded from:", dll_path)

# ================== PARAMETRI AWG ===========================
FREQUENCY_HZ      = 1500.0       # 1.5 kHz
DUTY_CYCLE_TARGET = 0.9998       # 99.98 %     
AMPLITUDE_VPP_V   = 1.39          # Volt picco-picco
OFFSET_V = -AMPLITUDE_VPP_V/2
WAVEFORM_SAMPLES  = 5000         # punti tabella AWG
# ============================================================


def main():
    status = {}

    # --------------------------------------------------------
    # 2) Apri il PicoScope (stessa logica di test_pico.py)
    # --------------------------------------------------------
    chandle = ctypes.c_int16()
    resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_8BIT"]

    status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)

    try:
        assert_pico_ok(status["openunit"])
    except:
        powerStatus = status["openunit"]
        if powerStatus in (286, 282):  # power supply / USB3 warning
            status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
            assert_pico_ok(status["changePowerSource"])
        else:
            raise

    print(f"PicoScope aperto, handle = {chandle.value}")

    try:
        # ----------------------------------------------------
        # 3) Info su limiti AWG
        # ----------------------------------------------------
        min_val = ctypes.c_int16()
        max_val = ctypes.c_int16()
        min_size = ctypes.c_uint32()
        max_size = ctypes.c_uint32()

        try:
            status["arbMinMax"] = ps.ps5000aSigGenArbitraryMinMaxValues(
                chandle,
                ctypes.byref(min_val),
                ctypes.byref(max_val),
                ctypes.byref(min_size),
                ctypes.byref(max_size),
            )
            assert_pico_ok(status["arbMinMax"])
            print(f"AWG sample range: [{min_val.value}, {max_val.value}]")
            print(f"AWG size range : [{min_size.value}, {max_size.value}]")
        except AttributeError:
            # Fallback
            min_val.value = -32768
            max_val.value = 32767
            min_size.value = 1
            max_size.value = 49152

        if WAVEFORM_SAMPLES < min_size.value or WAVEFORM_SAMPLES > max_size.value:
            raise RuntimeError(
                f"WAVEFORM_SAMPLES={WAVEFORM_SAMPLES} fuori range "
                f"[{min_size.value}, {max_size.value}]"
            )

        # ----------------------------------------------------
        # 4) Costruisci forma d’onda con duty ~99.98%
        # ----------------------------------------------------
        high_samples = int(round(WAVEFORM_SAMPLES * DUTY_CYCLE_TARGET))
        low_samples = WAVEFORM_SAMPLES - high_samples

        high_val = max_val.value
        low_val = min_val.value

        waveform = np.empty(WAVEFORM_SAMPLES, dtype=np.int16)
        waveform[:high_samples] = high_val
        waveform[high_samples:] = low_val

        actual_duty = np.count_nonzero(waveform == high_val) / WAVEFORM_SAMPLES
        print("\n=== INFO AWG / OUTPUT ===")
        print(f"Numero campioni    : {WAVEFORM_SAMPLES}")
        print(f"Campioni HIGH      : {high_samples}")
        print(f"Campioni LOW       : {low_samples}")
        print(f"Duty target        : {DUTY_CYCLE_TARGET * 100:.5f}%")
        print(f"Duty effettivo     : {actual_duty * 100:.5f}%")
        print(f"Valore HIGH (DAC)  : {high_val}")
        print(f"Valore LOW  (DAC)  : {low_val}")
        print("Primi 40 campioni:", waveform[:40])

        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

        # ----------------------------------------------------
        # 5) Converte frequenza in deltaPhase e configura AWG
        # ----------------------------------------------------
        phase = ctypes.c_uint32()
        status["freqToPhase"] = ps.ps5000aSigGenFrequencyToPhase(
            chandle,
            ctypes.c_double(FREQUENCY_HZ),
            ctypes.c_int32(0),                      # PS5000A_SINGLE
            ctypes.c_uint32(WAVEFORM_SAMPLES),
            ctypes.byref(phase),
        )
        assert_pico_ok(status["freqToPhase"])
        print(f"\nDeltaPhase per {FREQUENCY_HZ} Hz: {phase.value}")

        offset_uV = int(OFFSET_V * 1e6)
        pk_to_pk_uV = int(AMPLITUDE_VPP_V * 1e6)

        start_delta_phase = phase
        stop_delta_phase = phase
        delta_phase_increment = ctypes.c_uint32(0)
        dwell_count = ctypes.c_uint32(0)

        PS5000A_UP = 0
        PS5000A_ES_OFF = 0
        PS5000A_SINGLE = 0
        PS5000A_SIGGEN_RISING = 0
        PS5000A_SIGGEN_NONE = 0

        shots = ctypes.c_uint32(0)
        sweeps = ctypes.c_uint32(0)

        status["setSigGenArb"] = ps.ps5000aSetSigGenArbitrary(
            chandle,
            ctypes.c_int32(offset_uV),            # offsetVoltage (µV)
            ctypes.c_uint32(pk_to_pk_uV),         # pkToPk (µV)
            start_delta_phase,                    # startDeltaPhase
            stop_delta_phase,                     # stopDeltaPhase
            delta_phase_increment,                # deltaPhaseIncrement
            dwell_count,                          # dwellCount
            awg_buffer_ptr,                       # arbitraryWaveform*
            ctypes.c_int32(WAVEFORM_SAMPLES),     # arbitraryWaveformSize
            ctypes.c_int32(PS5000A_UP),           # sweepType
            ctypes.c_int32(PS5000A_ES_OFF),       # operation
            ctypes.c_int32(PS5000A_SINGLE),       # indexMode
            shots,                                # shots
            sweeps,                               # sweeps
            ctypes.c_int32(PS5000A_SIGGEN_RISING),# triggerType
            ctypes.c_int32(PS5000A_SIGGEN_NONE),  # triggerSource
            ctypes.c_int16(0),                    # extInThreshold
        )
        assert_pico_ok(status["setSigGenArb"])

        print(
            f"\nAWG attivo: f = {FREQUENCY_HZ} Hz, "
            f"duty ≈ {actual_duty * 100:.5f}%, offset = {OFFSET_V} V, "
            f"amp = {AMPLITUDE_VPP_V} Vpp"
        )
        input("\nCollega l’uscita AWG al CANALE A.\n"
              "Quando sei pronto premi Invio per acquisire...")

        # ----------------------------------------------------
        # 6) CONFIGURAZIONE CANALE A + ACQUISIZIONE
        #    (basata sul tuo test_pico.py)
        # ----------------------------------------------------
        channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        coupling_type = ps.PS5000A_COUPLING["PS5000A_DC"]
        # Range di ingresso: 2 V (adatta se serve)
        chARange = ps.PS5000A_RANGE["PS5000A_2V"]

        status["setChA"] = ps.ps5000aSetChannel(
            chandle, channelA, 1, coupling_type, chARange, 0
        )
        assert_pico_ok(status["setChA"])

        # disabilita B, C, D
        for ch_name in ["PS5000A_CHANNEL_B", "PS5000A_CHANNEL_C", "PS5000A_CHANNEL_D"]:
            ch = ps.PS5000A_CHANNEL[ch_name]
            status[f"set{ch_name[-1]}"] = ps.ps5000aSetChannel(
                chandle, ch, 0, coupling_type, chARange, 0
            )

        # max ADC
        maxADC = ctypes.c_int16()
        status["maximumValue"] = ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
        assert_pico_ok(status["maximumValue"])

        # Trigger semplice su CH A, soglia ~0 mV, auto 1000 ms
        source = channelA
        threshold = int(mV2adc(0, chARange, maxADC))
        direction = 2  # PS5000A_RISING
        delay = 0
        auto_trigger = 1000  # ms
        status["trigger"] = ps.ps5000aSetSimpleTrigger(
            chandle, 1, source, threshold, direction, delay, auto_trigger
        )
        assert_pico_ok(status["trigger"])

        # Campioni da acquisire
        preTriggerSamples = 0
        postTriggerSamples = 2000
        maxSamples = preTriggerSamples + postTriggerSamples

        # Timebase
        timebase = 3  # come nel tuo script; puoi cambiare se vuoi
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        status["getTimebase2"] = ps.ps5000aGetTimebase2(
            chandle,
            timebase,
            maxSamples,
            ctypes.byref(timeIntervalns),
            ctypes.byref(returnedMaxSamples),
            0,
        )
        assert_pico_ok(status["getTimebase2"])
        print(f"\nTimebase={timebase}, dt ≈ {timeIntervalns.value} ns")

        # Avvia acquisizione
        status["runBlock"] = ps.ps5000aRunBlock(
            chandle,
            preTriggerSamples,
            postTriggerSamples,
            timebase,
            ctypes.byref(ctypes.c_int32(0)),
            0,
            None,
            None,
        )
        assert_pico_ok(status["runBlock"])

        # Attendi fine acquisizione
        ready = ctypes.c_int16(0)
        while ready.value == 0:
            status["isReady"] = ps.ps5000aIsReady(chandle, ctypes.byref(ready))

        # Buffer dati
        bufferAMax = (ctypes.c_int16 * maxSamples)()
        bufferAMin = (ctypes.c_int16 * maxSamples)()

        status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(
            chandle,
            channelA,
            ctypes.byref(bufferAMax),
            ctypes.byref(bufferAMin),
            maxSamples,
            0,
            0,
        )
        assert_pico_ok(status["setDataBuffersA"])

        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(maxSamples)

        status["getValues"] = ps.ps5000aGetValues(
            chandle,
            0,
            ctypes.byref(cmaxSamples),
            0,
            0,
            0,
            ctypes.byref(overflow),
        )
        assert_pico_ok(status["getValues"])

        # ----------------------------------------------------
        # 7) CONVERSIONE E PLOT
        # ----------------------------------------------------
        data_mV = adc2mV(bufferAMax, chARange, maxADC)
        time_ns = np.linspace(
            0,
            (cmaxSamples.value - 1) * timeIntervalns.value,
            cmaxSamples.value,
        )

        plt.figure()
        plt.plot(time_ns * 1e-3, data_mV)  # x in µs
        plt.xlabel("Tempo (µs)")
        plt.ylabel("Volt (mV)")
        plt.title("Canale A - impulso AWG")
        plt.grid(True)
        plt.show()

        # Stop acquisizione (l’AWG smetterà quando chiudi l’unità)
        status["stop"] = ps.ps5000aStop(chandle)
        assert_pico_ok(status["stop"])

    finally:
        status["close"] = ps.ps5000aCloseUnit(chandle)
        assert_pico_ok(status["close"])
        print("PicoScope chiuso.")


if __name__ == "__main__":
    main()
