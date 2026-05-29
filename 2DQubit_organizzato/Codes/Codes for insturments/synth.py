import numpy as np
import pyvisa as pyvisa
import matplotlib.pyplot as plt 
import time
from typing import Literal
import serial
   
class class_SYNTH(serial.Serial):
    

    debug = True
    debug_prefix = ""

    def __init__(self, name, baudrate=9600):
        # Il Valon di solito lavora a 9600 o 115200 baud. Specificalo se necessario.
        self._LO = serial.Serial(name, baudrate=baudrate, timeout=1.0)  
        self._LO.flushInput() 
        if not self._LO.is_open: 
            raise Exception("Connection failed.")


    def write(self, unterminated_command):
        # Il Valon accetta \r, \n o \r\n. Manteniamo \r\n per sicurezza.
        command_utf8 = (unterminated_command + "\r\n").encode(encoding="utf-8")
        self._LO.write(command_utf8)

        if self.debug: 
            print(f"{self.debug_prefix}[WRITE]: {unterminated_command}")

    def query(self, unterminated_command):    
        command_utf8 = (unterminated_command + "\r\n").encode(encoding="utf-8")
        self._LO.write(command_utf8)
        
        # Nota: il Valon potrebbe fare l'echo del comando prima di dare la risposta.
        # Se noti che query() ti restituisce il comando stesso, andrà fatto un doppio readline().
        string = self._LO.readline().decode("utf-8").strip()

        if self.debug: 
            print(f"{self.debug_prefix}[QUERY]: {unterminated_command} -> {string}")

        return string
    
    def get_IDN(self):
        return self.query("ID")
    
    def get_stat(self):
        return self.query("OEN")
    
    def get_source_stat(self):
        return self.query("REF")

    def turn_on(self):
        self.write("OEN 1") # 1 = Output Enabled
    
    def turn_off(self):
        self.write("OEN 0") # 0 = Output Disabled
    
    def get_pot(self):
        return self.query("PWR")
    
    def get_freq(self):
        return self.query("FREQ")

    def set_freq(self, f_hz):
        """Set synthesized frequency. Input f_hz is in Hz"""
        # Il Valon ragiona in MHz. Convertiamo gli Hz in MHz (es. 2.4 GHz = 2400.0 MHz)
        f_mhz = f_hz / 1000000.0 
        
        self.write(f"FREQ {f_mhz}")
        time.sleep(0.05) # Un leggero delay aiuta il sintetizzatore ad agganciare (lock)
        self.freq = f_hz

        # Rimossa la conversione int() rigida sulla query di controllo, 
        # perché il Valon risponde spesso con stringhe formattate (es. "FREQ 2400.0000 MHz")
        risposta = self.query("FREQ")
        print(f"Verifica frequenza: {risposta}")            

    def set_pow(self, pow_dbm):
        """Set power in dBm"""
        self.write(f"PWR {pow_dbm}")
        time.sleep(0.01)
        self.pow = pow_dbm