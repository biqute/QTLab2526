#
# BLOCK MODE con acquisizione 100 MHz + FFT + salvataggio file
#
import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
import sys
sys.path.append("../classes")
from data import Data
from AWG import AWG

myAWG = AWG(ip_address="193.206.156.10") # Check IP: Utility > Interface > LAN Setup > IP Address
myAWG.timeout = 10e3
myAWG.set_waveform(1, "SINE")

myAWG.set_freq = 5000 # Hz
myAWG.set_amp = 0.5 # Vpp

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
postTriggerSamples = 200
maxSamples = preTriggerSamples + postTriggerSamples
timebase = 15 # ~1 ns

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
data_mV_A = adc2mV(bufferA_np, chRange, maxADC)
time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

file_name = "AWG_gaus_data"

# Salvataggio file
np.savetxt("../data/"+file_name+".txt", np.column_stack((time, data_mV_A)),
           header="Time(ns)\tVoltage(mV)-A\tVoltage(mV)-B", fmt="%.6f")
print("File "+file_name+".txt salvato.")

# ---------------------------------------------------------
#            FFT (For A)
# ---------------------------------------------------------
fs = 1e9 / timeIntervalns.value
N = len(data_mV_A)

window = np.hanning(N)
signal = data_mV_A * window

fft_vals = np.fft.fft(signal)
fft_freq = np.fft.fftfreq(N, d=timeIntervalns.value * 1e-9)

half = N // 2
fft_mag = np.abs(fft_vals[:half])
fft_freq = fft_freq[:half]

# ---------------------------------------------------------
#            PLOT
# ---------------------------------------------------------


# ---------------------------------------------------------
#            STOP E CHIUSURA
# ---------------------------------------------------------
status["stop"] = ps.ps5000aStop(chandle)
status["close"] = ps.ps5000aCloseUnit(chandle)

plt.figure(figsize=(10, 5))
plt.title("Gaussian Waveform")
plt.xlabel("Time")
plt.ylabel("Signal")
plt.plot(time, data_mV_A
         #,'-o', color='blue', 
         # label='Gaussian Waveform'
         ) 
        
plt.show()

save_as = "AWG_gaus_plot"
save_as += ".pdf"
plt.savefig(f"../data0_plots/{save_as}", bbox_inches="tight")
print(f"Grafico salvato in ../data/{save_as}")

print("Acquisizione completata.")
