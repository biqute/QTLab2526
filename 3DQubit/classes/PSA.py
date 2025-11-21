import pyvisa
import numpy as np


class PSA:
    _name = ""

    def __init__(self, ip_address_string):
        res_manager = pyvisa.ResourceManager()
        self.__res = res_manager.open_resource(f"tcpip0::{ip_address_string}::INSTR")

        self.__res.write("*CLS") # clear settings
        self._name = self.__res.query("*IDN?")

        res = self.__res.query("INST:SEL 'SA'; *OPC?")  # Spectrum Analyzer
        if res[0] != '1': raise Exception("Failed to select SA mode.")
        
        self.set_timeout(10e3)

    def set_timeout(self, millis):
        """
        Set request response timeout (in milliseconds)
        """
        self.__res.timeout = millis

    def set_point_count(self, n):
        """
        Set the number of datapoints
        """
        self.__res.write("SENS:SWE:POIN " + str(n))
        return self.__res.query("*OPC?")

    def set_min_freq(self, n):
        """
        Set minimum frequency in Hz
        """
        self.__res.write("SENS:FREQ:START " + str(n))
        return self.__res.query("*OPC?")

    def set_max_freq(self, n):
        """
        Set maximum frequency in Hz
        """
        self.__res.write("SENS:FREQ:STOP " + str(n))
        return self.__res.query("*OPC?")
    
    def read_data(self):
        """
        Returns the data displayed on the PSA as an array of floats 
        """
        return np.array(list(map(float, self.__res.query("TRACE:DATA?").split(","))))
