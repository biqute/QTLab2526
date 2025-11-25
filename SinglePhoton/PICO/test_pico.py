import os, ctypes
from picosdk.ps5000 import ps5000 as ps

dll_path = r"C:\Program Files\Pico Technology\SDK\lib"
os.add_dll_directory(dll_path)

chandle = ctypes.c_int16()
resolution = 8

status = ps.ps5000OpenUnit(ctypes.byref(chandle))
print("Status:", hex(status))
