import numpy as np
import pyvisa as pv
import math
from ethernetdevice import EthernetDevice


class VNA(EthernetDevice):
    """
    Vector Network Analyzer (VNA)

    Proprietà:
    - min_freq
    - max_freq
    - point_count
    - bandwidth
    - avg_count
    - power

    Metodi:
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
        self.write_expect("*CLS")                      # Pulisci le impostazioni
        self.write_expect("INST:SEL 'NA'")             # Seleziona modalità Network Analyzer
        self.write_expect("SENS:AVER:MODE SWEEP")      # Media su sweep
        self.write_expect("DISP:WIND:TRAC1:Y:AUTO")    # Autoscale asse Y

        # Impostazioni iniziali
        self.timeout = 600e3
        self.min_freq = 8.6356e9 
        self.max_freq = 8.6452e9
        self.point_count = 1000
        self.bandwidth = 1000      # Hz
        self.avg_count = 10
        self.power = -1            # dBm

        # Per vedere bene la risonanza:
        # self.min_freq = 4.84e9
        # self.max_freq = 6.4e9

    # ---------- MIN_FREQ ----------

    @property
    def min_freq(self):
        return self.__min_freq

    @min_freq.setter
    def min_freq(self, f):
        """Set minimum frequency in Hz"""
        self.write_expect(f"SENS:FREQ:START {f}")
        self.__min_freq = f

        ans = float(self.query("SENS:FREQ:START?").strip())
        if not math.isclose(ans, float(f), rel_tol=1e-6, abs_tol=0.0):
            raise Exception(f"Could not set 'min_freq' to {f}. Instrument returned {ans}.")

    # ---------- MAX_FREQ ----------

    @property
    def max_freq(self):
        return self.__max_freq

    @max_freq.setter
    def max_freq(self, f):
        """Set maximum frequency in Hz"""
        self.write_expect(f"SENS:FREQ:STOP {f}")
        self.__max_freq = f

        ans = float(self.query("SENS:FREQ:STOP?").strip())
        if not math.isclose(ans, float(f), rel_tol=1e-6, abs_tol=0.0):
            raise Exception(f"Could not set 'max_freq' to {f}. Instrument returned {ans}.")

    # ---------- POINT_COUNT ----------

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

    # ---------- BANDWIDTH ----------

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

    # ---------- AVERAGE COUNT ----------

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

    # ---------- POWER ----------

    @property
    def power(self):
        return self.__power

    @power.setter
    def power(self, value):
        """Set output power in dBm"""
        self.write_expect(f"SOUR:POW {value}")
        self.__power = value

        if float(self.query("SOUR:POW?").strip()) != float(value):
            raise Exception(f"Could not set 'power' to {value}.")

    # ---------- FREQUENCY SPECTRUM ----------

    def read_frequency_data(self):
        """Return frequency axis as numpy array."""
        resp = self.query_expect("FREQ:DATA?", "Frequency data readout failed.")
        return np.array(list(map(float, resp.split(","))))

    # ---------- DATA ACQUISITION ----------

    def read_data(self, Sij):
        """Read complex S-parameter data. Sij is 'S11', 'S12', 'S21' or 'S22'."""
        # Imposta il parametro
        self.write_expect("INIT:CONT 0")          # no continuous sweep
        self.write_expect(f"CALC:PAR:DEF {Sij}")  # scegli S-parameter

        # Fai le medie
        for i in range(self.avg_count):
            self.write_expect("INIT:IMMediate")
            if (i + 1) % 10 == 0 or i == 0 or i == self.avg_count - 1:
                print(f"[INIT:IMMediate] 1  ← media {i+1}/{self.avg_count}")

        # Leggi i dati complessi
        resp = self.query_expect("CALC:DATA:SDATA?", "Data readout failed.")
        data = np.array(list(map(float, resp.split(","))))
        data_real = data[0::2]   # 0,2,4,...
        data_imag = data[1::2]   # 1,3,5,...

        return {"real": data_real, "imag": data_imag}
