import numpy as np
import pyvisa as pv 

class VNA():
    def __init__(self, ip_address) :
        
        rm = pv.ResourceManager ()
        self._VNA = rm.open_resource("TCPIP0::"+ip_address+"::inst0::INSTR")
        self._VNA.write("*CLS")
        VNA =self._VNA.query("INST:SEL 'NA'; *OPC?")
        if VNA[0] != '1': raise Exception("Failed to select NA mode")


    def get_IDN(self):
        a = self._VNA.query("*IDN?") 
        print(a)
    
    def set_freq_minmax (self, min, max) :
        self._VNA.write(f'FREQ:STAR {min}')
        self._VNA.write(f'FREQ:STOP {max}')

        return self._VNA.query("*OPC?")

    def set_freq_center (self, center, span) :
        self._VNA.write(f'FREQ:CENT {center}')
        self._VNA.write(f'FREQ:SPAN {span}')

        return self._VNA.query("*OPC?")

    def set_points (self, num):
        if num<10000 :
            self._VNA.write(f'SWE:POIN {num}')
        else :
            raise ValueError("The number of points must be lower than 10000")
        
        return self._VNA.query("*OPC?")

    
    def set_average (self, aver):
        if aver<10000 :
            self._VNA.write(f'AVER:COUN {aver}')
        else :
            raise ValueError("The average must be lower than 10000")
        
        return self._VNA.query("*OPC?")
        
    def set_power (self, pow):
        if pow<=3 :
            self._VNA.write(f'SOUR:POW {pow}')
        else :
            raise ValueError("The source power must be lower than 3")
        
        return self._VNA.query("*OPC?")
    
    def set_sweep_time (self, time):
        if time<=4 :
            self._VNA.write(f'SWE:TIME {time}')
        else :
            raise ValueError("The sweep time must be lower than 4")
        
        return self._VNA.query("*OPC?")
    