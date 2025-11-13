import numpy as np
import pyvisa as pyvisa
import matplotlib.pyplot as plt 
import time
import os
from data import Data

class VNA():
    def __init__(self, ip):
        
        rm = pyvisa.ResourceManager()
        self.__VNA = rm.open_resource(f"TCPIP0::{ip}::inst0::INSTR")
        
        self.__VNA.write("*CLS") # Reset internal status and clear the error queue 

        VNA_mode = self.__VNA.write("INST:SEL 'NA'")
        if VNA_mode[0] != '1': raise Exception("Failed to select NA mode")
        
        self.__VNA.write("AVER:MODE POINT") # Average mode set to sweep
        self.__VNA.write("DISP:WIND:TRAC1:Y:AUTO") # Turn on autoscaling on the y axis
        
    def off(self):
        try:
            self.__VNA.clear()  # Pulisce il buffer
        finally:
            self.__VNA.close()  # Chiude la connessione

    def wait_for_opc(self, timeout=300):
        """
        Metodo generale per attendere il completamento del comando inviato tramite *OPC.
        
        :param timeout: Tempo massimo (in secondi) da attendere prima di sollevare un TimeoutError.
        """
        start_time = time.time()
        while True:
            status = self.__VNA.query("*OPC?")  # Interroga lo stato del comando *OPC
            if status.strip() == '1':  # Se la risposta è '1', l'operazione è completata
                return True
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout: l'operazione non è stata completata.")
            time.sleep(0.5)  # Pausa prima di verificare di nuovo

    def wait(self, wait_time):
        time.sleep(wait_time)  # Attende il tempo specificato


    def set_freq_limits(self, min_freq, max_freq):
        self.__VNA.write(f'FREQ:STAR {min_freq}')
        self.__VNA.write(f'FREQ:STOP {max_freq}')
        self.__VNA.write('*OPC')  # Segna che i comandi sono stati inviati

        if self.wait_for_opc():
            print("Frequenza minima e massima inserite correttamente.")

    def set_freq_span(self, center, span):
        self.__VNA.write(f'FREQ:CENT {center}')
        self.__VNA.write(f'FREQ:SPAN {span}')
        self.__VNA.write('*OPC')

        if self.wait_for_opc():
            print("Frequenza centrale e span impostati correttamente.")
        
    def set_power(self, power_dbm):
        self.__VNA.write(f'SOUR:POW {power_dbm}')
        self.__VNA.write('*OPC')

        if self.wait_for_opc():
            print(f"Potenza impostata correttamente a {power_dbm} dBm.")

    def set_ifband(self, ifband):
        self.__VNA.write(f'BWID {ifband}')
        self.__VNA.write('*OPC')

        if self.wait_for_opc():
            print(f"Larghezza di banda IF impostata correttamente a {ifband} Hz.")

    def set_sweep_time(self, time):
        self.__VNA.write(f'SWE:TIME {time}')
        self.__VNA.write('*OPC')

        if self.wait_for_opc():
            print(f"Tempo di sweep impostato correttamente a {time} secondi.")

    def set_sweep_points(self, sweep_points):
        self.__VNA.write(f'SWE:POIN {sweep_points}')
        self.__VNA.write('*OPC')

        if self.wait_for_opc():
            print(f"Numero di punti di sweep impostato correttamente a {sweep_points}.")

    def set_n_means(self, n_means):
        self.__VNA.write(f"SENS:AVER:COUN {n_means}")
        self.__VNA.write('*OPC')

        if self.wait_for_opc():
            print(f"Numero di medie impostato correttamente a {n_means}.")
    
    #def get_IDN(self):
    #    a = self.__VNA.query("*IDN?")
    #    print(a)
        
    def get_S_parameters(self, Sij):
        
        self.__VNA.write(f"CALC:PAR:DEF {Sij}")
        
        # Dati formattati (Reale, Immaginario)
        data_str = self.__VNA.query("CALC:DATA:SDATA?")
        data = np.array(list(map(float, data_str.split(","))))
        
        real = np.array(data[0::2])
        imag = np.array(data[1::2])
        return real, imag
    
    def get_power(self):
        real, imag = self.get_S_parameters()
        return np.array(real**2 + imag**2)
    
    def get_phase(self):
        real, imag = self.get_S_parameters()
        phase = np.unwrap(np.arctan2(imag, real))
        return phase
    
    def get_dbm(self):
        Pow = self.get_power()
        return np.array(10*np.log10(Pow))
    
    def get_freq(self):
        freq_str = self.__VNA.query("FREQ:DATA?")
        return list(map(float, freq_str.split(",")))

    """def get_spectrum(self) :
        print("Inizio acquisizione dati...")
        fig, ax = plt.subplots()
        
        # Trigger singolo e attesa di completamento
        self.__VNA.write("INIT:IMM; *WAI")
        
        freq = self.get_freq()
        Pow = self.get_dbm()
        print("Dati ricevuti. Plotting...")

        plt.title("Spettro S21")
        plt.xlabel("Frequenza [Hz]")
        plt.ylabel("Ampiezza [dBm]")
        ax.plot(freq, Pow)
        plt.grid(True)
        plt.show()

        return self.__VNA.query("*OPC?") """
    
    
