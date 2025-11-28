import os
import ctypes
import numpy as np

# Forza Python a caricare le DLL dalla cartella corrente
dll_path = os.path.abspath(os.path.dirname(__file__))
os.add_dll_directory(dll_path)
print("DLL loaded from:", dll_path)

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

# ----------------------------------------------------------------------
# PARAMETRI CONFIGURABILI
# ----------------------------------------------------------------------

CHANNEL = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
COUPLING = ps.PS5000A_COUPLING["PS5000A_DC"]
V_RANGE = ps.PS5000A_RANGE["PS5000A_20V"]

POSTTRIGGER = 5000       # Numero di punti per blocco
TRIGGER_LEVEL_MV = 5     # Trigger in mV
HW_RESOLUTION = "PS5000A_DR_14BIT"  # Risoluzione hardware
NUM_AVG = 10             # Numero di blocchi da mediare

# ----------------------------------------------------------------------
# APERTURA STRUMENTO
# ----------------------------------------------------------------------

chandle = ctypes.c_int16()
status = {}

resolution = ps.PS5000A_DEVICE_RESOLUTION[HW_RESOLUTION]
status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)
assert_pico_ok(status["openunit"])

# ----------------------------------------------------------------------
# CONFIGURAZIONE CANALE
# ----------------------------------------------------------------------

status["setChA"] = ps.ps5000aSetChannel(chandle, CHANNEL, 1, COUPLING, V_RANGE, 0)
assert_pico_ok(status["setChA"])

# ----------------------------------------------------------------------
# TRIGGER
# ----------------------------------------------------------------------

maxADC = ctypes.c_int16()
status["maxADC"] = ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
assert_pico_ok(status["maxADC"])

thr_adc = int(mV2adc(TRIGGER_LEVEL_MV, V_RANGE, maxADC))
status["trigger"] = ps.ps5000aSetSimpleTrigger(
    chandle, 1, CHANNEL, thr_adc, 2, 0, 1000
)
assert_pico_ok(status["trigger"])

# ----------------------------------------------------------------------
# SELEZIONE AUTOMATICA TIMEBASE
# ----------------------------------------------------------------------

timeInterval = ctypes.c_float()
returnedMaxSamples = ctypes.c_int32()

timebase = 0
while True:
    status_tb = ps.ps5000aGetTimebase2(
        chandle,
        timebase,
        POSTTRIGGER,
        ctypes.byref(timeInterval),
        ctypes.byref(returnedMaxSamples),
        0
    )
    if status_tb == 0:  # PICO_OK
        if POSTTRIGGER <= returnedMaxSamples.value:
            print(f"Timebase scelto automaticamente: {timebase}")
            break
        else:
            POSTTRIGGER = returnedMaxSamples.value
            print(f"PostTrigger ridotto a {POSTTRIGGER}")
            break
    timebase += 1
    if timebase > 20:
        raise Exception("Nessun timebase valido trovato per il numero di punti richiesto")

# ----------------------------------------------------------------------
# ACQUISIZIONE MULTIPLA E MEDIA
# ----------------------------------------------------------------------

avg_data = np.zeros(POSTTRIGGER, dtype=float)

for i in range(NUM_AVG):
    # Run block
    status["runBlock"] = ps.ps5000aRunBlock(
        chandle,
        0, POSTTRIGGER,
        timebase,
        None, 0, None, None
    )
    assert_pico_ok(status["runBlock"])

    # Wait until ready
    ready = ctypes.c_int16(0)
    while ready.value == 0:
        ps.ps5000aIsReady(chandle, ctypes.byref(ready))

    # Setup buffer
    bufferA = (ctypes.c_int16 * POSTTRIGGER)()
    status["setBuffer"] = ps.ps5000aSetDataBuffers(
        chandle, CHANNEL, bufferA, None, POSTTRIGGER, 0, 0
    )
    assert_pico_ok(status["setBuffer"])

    # Get values
    samples = ctypes.c_int32(POSTTRIGGER)
    overflow = ctypes.c_int16()
    status["getValues"] = ps.ps5000aGetValues(
        chandle, 0, ctypes.byref(samples), 0, 0, 0, ctypes.byref(overflow)
    )
    assert_pico_ok(status["getValues"])

    # Converti in mV
    data_mV = adc2mV(bufferA, V_RANGE, maxADC)
    data_mV = np.array(data_mV, dtype=float)

    # Somma per la media
    avg_data += data_mV

# Calcola media finale
avg_data /= NUM_AVG

# Calcola media, std, errore standard
mean_v = np.mean(avg_data)
std_v = np.std(avg_data)
stderr_v = std_v / np.sqrt(len(avg_data))

print("\n-------------------------------------")
print("   RISULTATI MISURA DI VOLTAGGIO (media 10 blocchi)")
print("-------------------------------------")
print(f"Numero di punti      : {len(avg_data)}")
print(f"Media (mV)           : {mean_v:.6f}")
print(f"Deviazione std (mV)  : {std_v:.6f}")
print(f"Errore standard (mV) : {stderr_v:.6f}")
print(f"Intervallo tempo (ns): {timeInterval.value:.2f}")
print("-------------------------------------\n")

# ----------------------------------------------------------------------
# CHIUSURA
# ----------------------------------------------------------------------

ps.ps5000aStop(chandle)
ps.ps5000aCloseUnit(chandle)
