import numpy as np
import pyvisa as pv 

class VNA():
    def __init__(self, ip_address) :
        
        rm = pv.ResourceManager ()
        self._VNA = rm.open_resource("TCPIP0::"+ip_address+"::inst0::INSTR")

    def get_IDN(self):
        a = self._VNA.query("*IDN?") 
        print(a)
    
    def 