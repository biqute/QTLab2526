import ctypes
import os
from picosdk.ps5000 import ps5000 as ps

# Aggiungi la cartella delle DLL al PATH di Windows
dll_path = r"C:\Program Files\Pico Technology\SDK\lib"
os.add_dll_directory(dll_path)

# Handle della scheda
chandle = ctypes.c_int16()

# Imposta la risoluzione (8-bit)
resolution = 8  # 8-bit resolution

# Prova ad aprire il PicoScope con la risoluzione di default (8-bit)
status = ps.ps5000OpenUnit(ctypes.byref(chandle))

if status == 0:
    print("✅ PicoScope trovato! Handle:", chandle.value)
    # Chiudi subito l'unità
    ps.ps5000CloseUnit(chandle)
else:
    print("❌ Connessione fallita. Status:", status)
