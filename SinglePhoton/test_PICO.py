import os
import ctypes
from picosdk.ps5000 import ps5000 as ps
import matplotlib.pyplot as plt
import numpy as np
import time

dll_folder = r"C:\Program Files\Pico Technology\SDK\lib"
dlls = ["ps5000.dll", "picoipp.dll"]

print("🔎 Controllo DLL...")
for dll in dlls:
    path = os.path.join(dll_folder, dll)
    if os.path.exists(path):
        print(f"✅ DLL trovata: {dll}")
    else:
        print(f"❌ DLL mancante: {dll}")

os.add_dll_directory(dll_folder)

for dll in dlls:
    try:
        ctypes.cdll.LoadLibrary(os.path.join(dll_folder, dll))
        print(f"✅ Caricata correttamente: {dll}")
    except Exception as e:
        print(f"❌ Errore caricamento {dll}: {e}")

print("\n🔎 Verifica PicoScope tramite PS5000...")
chandle = ctypes.c_int32()
status = ps.ps5000OpenUnit(ctypes.byref(chandle))
if status != 0:
    print(f"❌ PicoScope non trovato. Status: {status}")
    exit()

handle = chandle.value
print(f"✅ PicoScope rilevato! Handle: {handle}")

# --- Configura canale A ---
ps.ps5000SetChannel(handle, 0, 1, 1, 0)  # channel=0, enabled=1, DC=1, range=0

# --- Configura acquisizione ---
max_samples = 1000
data = np.zeros(max_samples, dtype=np.int16)
ps.ps5000SetDataBuffer(handle, 0, data.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)), max_samples, 0, 0)

# --- Avvia acquisizione ---
ps.ps5000RunBlock(handle, max_samples, 1, 0, 0, None, 0, None, 0)

# Aspetta completamento
ready = ctypes.c_int16(0)
while ready.value == 0:
    ps.ps5000IsReady(handle, ctypes.byref(ready))
    time.sleep(0.01)

# --- Leggi dati ---
actual_samples = ctypes.c_int32()
overflow = ctypes.c_int16()
ps.ps5000GetValues(handle, 0, ctypes.byref(actual_samples), 1, 0, 0, ctypes.byref(overflow))

print(f"Campioni letti: {actual_samples.value}, Overflow: {overflow.value}")

# --- Plotta ---
plt.plot(data[:actual_samples.value])
plt.title("Acquisizione Canale A")
plt.xlabel("Campione")
plt.ylabel("Valore ADC")
plt.show()

# --- Chiudi ---
ps.ps5000CloseUnit(handle)
print("✅ PicoScope chiuso")
