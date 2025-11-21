import ctypes
import os

dll_path = r"C:\Program Files\Pico Technology\SDK\lib\ps5000a.lib"
os.add_dll_directory(dll_path)

try:
    ctypes.cdll.LoadLibrary(r"C:\Program Files\Pico Technology\SDK\lib\picoipp.dll")
    print("✅ DLL caricate correttamente")
except OSError as e:
    print("❌ Errore caricamento DLL:", e)

