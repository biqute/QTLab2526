import numpy as np
import pyvisa as pv
from ethernetdevice import EthernetDevice


class VNA(EthernetDevice):
    """
    Vector Network Analyzer (VNA)

    La classe ha le seguenti proprietà
    - min_freq 
    - max_freq 
    - point_count 
    - bandwidth 
    - avg_count 
    - power 

    La classe ha i seguenti metodi:
    - read_frequency_data
    - read_data
    """

    __min_freq = 0
    __max_freq = 0
    __point_count = 0
    __bandwidth = 0
    __avg_count = 0
    __power = 0

    def on_init(self, ip_address_string=None):
        self.write_expect("*CLS")  # Pulisci le impostazioni
        self.write_expect("INST:SEL 'NA'")  # Seleziona la modalità Network Analyzer
        self.write_expect("SENS:AVER:MODE SWEEP")  # Imposta la modalità di media a sweep
        self.write_expect("DISP:WIND:TRAC1:Y:AUTO")  # Attiva l'autoscaling sull'asse Y
        
        # Impostazioni iniziali
        self.timeout = 10e3
        self.min_freq = 4.0e9
        self.max_freq = 4.110e9
        self.point_count = 1000
        self.bandwidth = 1000  # Hz
        self.avg_count = 100
        self.power = -1  # dBm

    
    # MIN_FREQ

    @property
    def min_freq(self):
        return self.__min_freq

    @min_freq.setter
    def min_freq(self, f):
        """Set minimum frequency in Hz"""
        self.write_expect(f"SENS:FREQ:START {f}")
        self.__min_freq = f

        if int(self.query("SENS:FREQ:START?")) != f: 
            raise Exception(f"Could not set 'min_freq' to {f}.")


    # MAX_FREQ

    @property
    def max_freq(self):
        return self.__max_freq

    @max_freq.setter
    def max_freq(self, f):
        """Set maximum frequency in Hz"""
        self.write_expect(f"SENS:FREQ:STOP {f}")
        self.__max_freq = f

        if int(self.query("SENS:FREQ:STOP?")) != f: 
            raise Exception(f"Could not set 'max_freq' to {f}.")
    
    # POINT_COUNT
    
    @property
    def point_count(self):
        return self.__point_count
    
    @point_count.setter
    def point_count(self, n):
        """Set the number of datapoints"""
        self.write_expect(f"SENS:SWE:POIN {n}")
        self.__point_count = n

        if int(self.query("SENS:SWE:POIN?")) != n: 
            raise Exception(f"Could not set 'point_count' to {n}.")

    # BANDWIDTH

    @property
    def bandwidth(self):
        return self.__bandwidth
    
    @bandwidth.setter
    def bandwidth(self, bw):
        """Set the bandwidth in Hz"""
        self.write_expect(f"SENS:BWID {bw}")
        self.__bandwidth = bw

        if int(self.query("SENS:BWID?")) != bw: 
            raise Exception(f"Could not set 'bandwidth' to {bw}.")

    # AVERAGE COUNT

    @property
    def avg_count(self):
        return self.__avg_count
    
    @avg_count.setter
    def avg_count(self, n):
        """Set the number of averages (1 = no averages)"""
        self.write_expect(f"AVER:COUN {n}")
        self.__avg_count = n

        if int(self.query("AVER:COUN?")) != n: 
            raise Exception(f"Could not set 'avg_count' to {n}.")
        
    # POWER

    @property
    def power(self):
        return self.__power

    @power.setter
    def power(self, value):
        """Set output power in dBm"""
        self.write_expect(f"SOUR:POW {value}")
        self.__power = value

        if float(self.query("SOUR:POW?").strip()) != value: 
            raise Exception(f"Could not set 'power' to {value}.")

    # FREQUENCY SPECTRUM

    def read_frequency_data(self):
        return np.array(list(map(float, self.query_expect("FREQ:DATA?", "Frequency data readout failed.").split(","))))
        

    # DATA ACQUISITION
    
    def read_data(self, Sij):
        """Sij is a string of value "S11", "S12", "S21" or "S22"."""
        self.write_expect("INIT:CONT 0")
        self.write_expect(f"CALC:PAR:DEF {Sij}") # Chose which data to read

        for _ in range(self.avg_count): self.write_expect("INIT:IMMediate") # Trigger now
        
        data = np.array(list(map(float, self.query_expect("CALC:DATA:SDATA?", "Data readout failed.").split(","))))
        data_real = data[0::2] # all even entries 0,2,4,6,8
        data_imag = data[1::2] # all odd entries 1,3,5,7,9

        self.write_expect("INIT:CONT 1")

        return {"real": data_real, "imag": data_imag}
    
    # (...)

