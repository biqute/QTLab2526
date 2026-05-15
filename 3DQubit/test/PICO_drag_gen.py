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

# ================== PARAMETRI AWG ===========================
FREQUENCY_HZ      = 1500.0       #  Hz 
DUTY_CYCLE_TARGET = 0.1       # quanto sta sopra dell'onda quadra   
AMPLITUDE_VPP_V   = 1        # Volt picco-picco
# Offset per avere segnale tra 0V (High) e -1.39V (Low)
OFFSET_V          = 0
WAVEFORM_SAMPLES  = 30000         # punti tabella AWG

def generate_drag_pulse(samples, n_cycles, limit=3.0, beta=0.5):
    """
    Genera un impulso DRAG (Gaussiana + Derivata in quadratura) modulato su una portante.
    
    samples: numero di campioni totali nel buffer
    n_cycles: numero di cicli della portante
    limit: estensione temporale in unità di sigma (es. +/- 3 sigma per troncare la gaussiana)
    beta: parametro DRAG (scala l'ampiezza della derivata).
    """
    # Asse temporale normalizzato t/sigma (da -limit a +limit)
    t_rel = np.linspace(-limit, limit, samples)
    
    # Inviluppo I (In-Phase): Gaussiana standard
    I_env = np.exp(-0.5 * t_rel**2)
    
    # Inviluppo Q (Quadrature): Derivata della Gaussiana moltiplicata per beta
    # La derivata di exp(-t^2 / 2) rispetto a t è -t * exp(-t^2 / 2)
    Q_env = -beta * t_rel * I_env
    
    # Asse per la portante (da 0 a 1, per fare n_cycles interi)
    t_carrier = np.linspace(0, 1, samples)
    
    # Portanti ortogonali
    carrier_I = np.cos(2 * np.pi * n_cycles * t_carrier)
    carrier_Q = np.sin(2 * np.pi * n_cycles * t_carrier)
    
    # Miscelazione IQ (Up-conversion digitale)
    signal = I_env * carrier_I + Q_env * carrier_Q
    
    # Normalizzazione FONDAMENTALE per l'AWG:
    # L'AWG del PicoScope vuole valori tra -1.0 e 1.0 prima della moltiplicazione per max_val.
    # Poiché I e Q si sommano, il picco potrebbe superare 1.0.
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

        # ... (codice precedente: apertura unit, arbMinMax, ecc.)

# --- Setup AWG ---
        min_val, max_val = ctypes.c_int16(), ctypes.c_int16()
        ps.ps5000aSigGenArbitraryMinMaxValues(chandle, ctypes.byref(min_val), ctypes.byref(max_val), None, None)

        f_real = 15e3  # Portante a 15 kHz 
        N_OSCILLAZIONI = f_real / FREQUENCY_HZ
        
        # NUOVO: Parametro DRAG (inizia con un valore piccolo, ad es. 0.3 o 0.5)
        BETA_DRAG = 0.5 
        LIMIT_SIGMA = 3.0 # Tronca la gaussiana a +/- 3 sigma

        # Generazione impulso DRAG
        signal_float = generate_drag_pulse(WAVEFORM_SAMPLES, N_OSCILLAZIONI, LIMIT_SIGMA, BETA_DRAG)
        
        waveform = (signal_float * max_val.value).astype(np.int16)
        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
# Visualizziamo i parametri per debug
        print("\n=== INFO AWG (DRAG) ===")
        print(f"Frequenza Target: {FREQUENCY_HZ} Hz")
        print(f"Punti buffer: {WAVEFORM_SAMPLES}")

# Puntatore al buffer per la DLL
        awg_buffer_ptr = waveform.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))

# ... (prosegui con ps5000aSigGenFrequencyToPhase e il resto)

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
        # Perché il segnale è a 0V e scende a -1.4V
        threshold_adc = int(mV2adc(-200, chRange, maxADC))
        direction = 3 # PS5000A_FALLING
       
        status["trigger"] = ps.ps5000aSetSimpleTrigger(
            chandle, 1, channelA, threshold_adc, direction, 0, 1000
        )
        assert_pico_ok(status["trigger"])

        # ----------------------------------------------------
        # 5) Timebase e Acquisizione
        # ----------------------------------------------------
        # Timebase 127 a 16-bit corrisponde a circa 1000ns (1µs) per campione.
        # Con 5000 campioni => 5ms totali (vedrai ~7 cicli da 0.66ms l'uno)
        # Aumenta i campioni per vedere l'intera campana (1.5kHz = 666us di periodo)
        preTriggerSamples = 400
        postTriggerSamples = 400 
        timebase = 64 # Rallenta il campionamento per catturare più tempo
        totalSamples = preTriggerSamples + postTriggerSamples
       
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()

        status["getTimebase"] = ps.ps5000aGetTimebase2(
            chandle, timebase, totalSamples,
            ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0
        )
        assert_pico_ok(status["getTimebase"])
        print(f"Timebase: {timebase} (dt = {timeIntervalns.value} ns)")
        print(f"Durata acquisizione: {(timeIntervalns.value * totalSamples)/1e6:.2f} ms")

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
        # 6) Plot
        # ----------------------------------------------------
        data_mV = adc2mV(bufferMax, chRange, maxADC)
        time_axis = np.linspace(
            0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value
        )
        # --- SALVATAGGIO DATI SU FILE TXT ---
        # Creiamo una matrice con due colonne: Tempo e Tensione
        data_to_save = np.column_stack((time_axis/1000, data_mV))
        filename_txt = "../signalGen/drag_env_data.txt"
        np.savetxt(filename_txt, data_to_save, fmt='%.6f', header="Time(us) Voltage(mV)", delimiter='\t')
        print(f"Dati salvati in: {filename_txt}")
        plt.figure(figsize=(10, 6))
        plt.plot(time_axis / 1000.0, data_mV) # x in µs
        plt.xlabel("Time (µs)")
        plt.ylabel("Voltage (mV)")
        plt.title(f"PICO signal generation - {f_real} Hz")
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