import numpy as np
import pyvisa

class SDG() :
    def __init__(self, ip_address) :
        
        rm = pyvisa.ResourceManager ()
        self._SDG = rm.open_resource("TCPIP0::"+ip_address+"::inst0::INSTR")
        print('for all function the parameter order is ch, f, amp, phase, off')
    def set_freq(self, ch, f) :

        self._SDG.write(f'C{ch}'+f":BSWV FRQ,{f}")
    
    def set_amp(self, ch, amp) :

        self._SDG.write(f'C{ch}'+f":BSWV AMP,{amp}")
    
    def set_period(self, ch, per) :

        self._SDG.write(f'C{ch}'+f":BSWV PERI,{per}")
    
    def set_phase(self, ch, phase) :

        self._SDG.write(f'C{ch}'+f":BSWV PHSE,{phase}")
    
    def set_offset(self, ch, off) :

        self._SDG.write(f'C{ch}'+f":BSWV OFST,{off}")
        
    def set_formwave(self, ch, wtp) : #probably pass wtp as string

        self._SDG.write(f'C{ch}'+":BSWV WVTP,"+wtp)
    
    def set_all(self, ch, f, amp, phase, off) :

        self._SDG.write(f'C{ch}'+f":BSWV FREQ,{f},"+f'AMP,{amp},'+f'PHSE,{phase},'+f'OFST,{off}')

    def ask(self,msg_string): #general get function
        
        self._SDG.write(msg_string) #takes an already encoded string
        
        return self._SDG.readline().decode()
    
    def get_freq(self):

        f=self.ask('FREQ?')

        return float(f)
        