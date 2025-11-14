import numpy as np
import pyvisa
import re


class SDG_new() :
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

        self._SDG.write(f'C{ch}'+f":BSWV FRQ,{f},"+f'AMP,{amp},'+f'PHSE,{phase},'+f'OFST,{off}')

    def get_IDN(self) :

        a = self._SDG.query("*IDN?") 
        print(a)
        return a
    
    def turn_ON(self, ch) :

        self._SDG.write(f"C{ch}:OUTP ON") 
    
    def turn_OFF(self, ch) :
        
        self._SDG.write(f"C{ch}:OUTP OFF") 
    
    
    def get_value(self, ch=1, str = ''):
        response = self._SDG.query(f"C{ch}:BSWV?")
        if str == 'all' or str == 'ALL':
            return response
        
        else:
            if str.islower() == True : str = str.upper()

            parts = response.split(',')
            try:
                value_index = parts.index(str) + 1
                value_um = parts[value_index]
                match = re.match(r"([\d\.]+)\s*([a-zA-Zµμ]+)", value_um)

                if match:
                    value = float(match.group(1))
                    unit = match.group(2)
                    lista = [value, unit]
                return lista
            except ValueError:
                print("Parametro non ricevuto, verificare che sia tutto maiuscolo")
                print("Risposta ricevuta:", response)
            return None
        
    
    def modulation(self, value):
        """Turn ON and OFF the modulation"""
        # AM = amplitude modulation, MDSP = modulation wave shape, ARB = arbitrary
        if value == 'on':
            self._SDG.write(f"C1:MDWV STATE,ON")
            self._SDG.write(f"C1:MDWV AM")
            self._SDG.write(f"C1:MDWV AM,SRC,INT")
            self._SDG.write("C1:MDWV MDSP,SINE")
            print(self._SDG.query(f"*OPC?"))
        elif value == 'off':
            self._SDG.write(f"C1:MDWV STATE,OFF,AM,MDSP,ARB")
        else:
            raise ValueError("'value' parameter must be 'on' or 'off'")
        
    def set_mod_all(self, ch, f, amp, phase, off) :

        self._SDG.write(f'C{ch}'+f":BSWV FREQ,{f},"+f'AMP,{amp},'+f'PHSE,{phase},'+f'OFST,{off}')

        


