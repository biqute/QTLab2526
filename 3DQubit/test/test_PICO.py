#
# BLOCK MODE con acquisizione 100 MHz + FFT + salvataggio file
#

import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc

# ---------------------------------------------------------
#            APERTURA STRUMENTO
# ---------------------------------------------------------
chandle = ctypes.c_int16()
status = {}

resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]
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

# ---------------------------------------------------------
#            CONFIGURAZIONE CANALI
# ---------------------------------------------------------
channelA = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
coupling = ps.PS5000A_COUPLING["PS5000A_DC"]
chRange = ps.PS5000A_RANGE["PS5000A_2V"]

status["setChA"] = ps.ps5000aSetChannel(chandle, channelA, 1, coupling, chRange, 0)
assert_pico_ok(status["setChA"])

# Disattiva B, C, D
for ch in ["PS5000A_CHANNEL_B", "PS5000A_CHANNEL_C", "PS5000A_CHANNEL_D"]:
    ps.ps5000aSetChannel(chandle, ps.PS5000A_CHANNEL[ch], 0, coupling, chRange, 0)

# ---------------------------------------------------------
#            VALORE ADC MASSIMO
# ---------------------------------------------------------
maxADC = ctypes.c_int16()
status["maximumValue"] = ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
assert_pico_ok(status["maximumValue"])

# ---------------------------------------------------------
#            TRIGGER
# ---------------------------------------------------------
threshold = int(mV2adc(50, chRange, maxADC))  # 50 mV
status["trigger"] = ps.ps5000aSetSimpleTrigger(chandle, 1, channelA, threshold, 2, 0, 1000)
assert_pico_ok(status["trigger"])

# ---------------------------------------------------------
#        SAMPLES E TIMEBASE
# ---------------------------------------------------------
preTriggerSamples = 0
postTriggerSamples = 10
maxSamples = preTriggerSamples + postTriggerSamples
timebase = 315 # ~1 ns

timeIntervalns = ctypes.c_float()
returnedMaxSamples = ctypes.c_int32()

status["getTimebase2"] = ps.ps5000aGetTimebase2(
    chandle, timebase, maxSamples,
    ctypes.byref(timeIntervalns),
    ctypes.byref(returnedMaxSamples), 0
)
assert_pico_ok(status["getTimebase2"])
print("Intervallo di campionamento (ns):", timeIntervalns.value)

# ---------------------------------------------------------
#            BUFFER
# ---------------------------------------------------------
bufferA = (ctypes.c_int16 * maxSamples)()
bufferAmin = (ctypes.c_int16 * maxSamples)()

# SetDataBuffers **prima** di RunBlock
status["setDataBuffersA"] = ps.ps5000aSetDataBuffers(
    chandle, channelA,
    ctypes.byref(bufferA),
    ctypes.byref(bufferAmin),
    maxSamples, 0, 0
)
assert_pico_ok(status["setDataBuffersA"])

# ---------------------------------------------------------
#                 ACQUISIZIONE BLOCK MODE
# ---------------------------------------------------------
status["runBlock"] = ps.ps5000aRunBlock(
    chandle, preTriggerSamples, postTriggerSamples,
    timebase, None, 0, None, None
)
assert_pico_ok(status["runBlock"])

ready = ctypes.c_int16(0)
while ready.value == 0:
    status["isReady"] = ps.ps5000aIsReady(chandle, ctypes.byref(ready))

# ---------------------------------------------------------
#            LETTURA DATI
# ---------------------------------------------------------
cmaxSamples = ctypes.c_int32(maxSamples)
overflow = ctypes.c_int16()

status["getValues"] = ps.ps5000aGetValues(
    chandle, 0, ctypes.byref(cmaxSamples),
    0, 0, 0, ctypes.byref(overflow)
)
assert_pico_ok(status["getValues"])

# Conversione in numpy
bufferA_np = np.array(bufferA, dtype=np.int16)
data_mV = adc2mV(bufferA_np, chRange, maxADC)
time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

# Salvataggio file
np.savetxt("acquisizione.txt", np.column_stack((time, data_mV)),
           header="Time(ns)\tVoltage(mV)", fmt="%.6f")
print("File acquisizione.txt salvato.")

# ---------------------------------------------------------
#            FFT
# ---------------------------------------------------------
fs = 1e9 / timeIntervalns.value
N = len(data_mV)

window = np.hanning(N)
signal = data_mV * window

fft_vals = np.fft.fft(signal)
fft_freq = np.fft.fftfreq(N, d=timeIntervalns.value * 1e-9)

half = N // 2
fft_mag = np.abs(fft_vals[:half])
fft_freq = fft_freq[:half]

# ---------------------------------------------------------
#            PLOT
# ---------------------------------------------------------
plt.figure(figsize=(12,5))

# Segnale nel tempo (downsampling per leggibilità)
step = max(1, N//5000)
plt.subplot(1,2,1)
plt.plot(time[::step], data_mV[::step])
plt.title("Segnale nel tempo")
plt.xlabel("Tempo (ns)")
plt.ylabel("mV")

# FFT
plt.subplot(1,2,2)
plt.plot(fft_freq/1e6, fft_mag)
plt.title("FFT")
plt.xlabel("Frequenza (MHz)")
plt.ylabel("Ampiezza (a.u.)")
plt.xlim(0, 0.1)

plt.tight_layout()
plt.show()

# ---------------------------------------------------------
#            STOP E CHIUSURA
# ---------------------------------------------------------
status["stop"] = ps.ps5000aStop(chandle)
status["close"] = ps.ps5000aCloseUnit(chandle)

print("Acquisizione completata.")
