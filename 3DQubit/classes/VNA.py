import numpy as np
import pyvisa as pyvisa
import matplotlib.pyplot as plt 
import os
from data import Data

class VNA():
    def __init__(self, ip):
        
        rm = pyvisa.ResourceManager()
        # Assicurati che il tuo indirizzo VISA sia corretto
        self._VNA = rm.open_resource(f"TCPIP0::{ip}::inst0::INSTR")
        self._VNA.timeout = 10000
        
        self._VNA.write("*CLS")
        VNA_mode = self._VNA.query("INST:SEL 'NA'; *OPC?")
        if VNA_mode[0] != '1': raise Exception("Failed to select NA mode")
        
        self._VNA.write("AVER:MODE POINT") # Average mode set to sweep
        self._VNA.write("DISP:WIND:TRAC1:Y:AUTO") # Turn on autoscaling on the y axis
        self._VNA.write("CALC:SMO 0") # Smoothing off

        # --- IMPOSTAZIONE S21  ---
        self._VNA.write("CALC:PAR:DEF 'Trc1', 'S21'")
        self._VNA.write("DISP:WIND:TRAC1:FEED 'Trc1'")
        print("VNA inizializzato e configurato per S21 su Traccia 1.")
        
        self.average = 1

    def get_IDN(self):
        a = self._VNA.query("*IDN?")
        print(a)

    def set_freq_limits(self, min_freq, max_freq):
        self._VNA.write(f'FREQ:STAR {min_freq}')
        self._VNA.write(f'FREQ:STOP {max_freq}')
        return self._VNA.query("*OPC?")

    def set_freq_span(self, center, span):
        self._VNA.write(f'FREQ:CENT {center}')
        self._VNA.write(f'FREQ:SPAN {span}')
        return self._VNA.query("*OPC?")

    def set_sweep_points(self, num):
        self._VNA.write(f'SWE:POIN {num}')
        return self._VNA.query("*OPC?")
        
    def set_power(self, power_dbm):
        self._VNA.write(f'SOUR:POW {power_dbm}')
        return self._VNA.query("*OPC?")
    
    def set_sweep_time(self, time):
        self._VNA.write(f'SWE:TIME {time}')
        return self._VNA.query("*OPC?")
        
    def get_S_parameters(self) :
        
        self._VNA.write("CALC:PAR:SEL 'Trc1'")
        
        # Dati formattati (Reale, Immaginario)
        data_str = self._VNA.query("CALC:DATA:SDATA?")
        data = np.array(list(map(float, data_str.split(","))))
        
        real = np.array(data[0::2])
        imag = np.array(data[1::2])
        return real, imag
    
    def get_power(self) :
        real, imag = self.get_S_parameters()
        return np.array(real**2 + imag**2)
    
    def get_phase(self) :
        real, imag = self.get_S_parameters()
        phase = np.unwrap(np.arctan2(imag, real))
        return phase
    
    def get_dbm(self) :
        Pow = self.get_power()
        return np.array(10*np.log10(Pow))
    
    def set_average(self, n) :
        """Set the number of averages (1 = no averages)"""
        self._VNA.write(f"AVER:COUN {n}")
        self.average = n

        if int(self._VNA.query("AVER:COUN?")) != n: 
            raise Exception(f"Could not set 'avg_count' to {n}.")
    
    def get_freq(self) :
        # Comando SCPI più standard per l'asse X (frequenza)
        freq_str = self._VNA.query("SENS:FREQ:DATA?")
        return list(map(float, freq_str.split(",")))

    def get_spectrum(self) :
        print("Inizio acquisizione dati...")
        fig, ax = plt.subplots()
        
        # Trigger singolo e attesa di completamento
        self._VNA.write("INIT:IMM; *WAI")
        
        freq = self.get_freq()
        Pow = self.get_dbm()
        print("Dati ricevuti. Plotting...")

        plt.title("Spettro S21")
        plt.xlabel("Frequenza [Hz]")
        plt.ylabel("Ampiezza [dBm]")
        ax.plot(freq, Pow)
        plt.grid(True)
        plt.show()

        return self._VNA.query("*OPC?")
    
    def save_data(self, Sij, filename):
        """
        Esegue la misura e usa la classe Data per salvare i risultati.
        
        Args:
            Sij (str): Parametro S da misurare (es. "S21").
            filename (str): Nome file *senza* estensione (es. "mia_misura").
                            Verrà salvato in ../data/mia_misura.txt
        """
        print(f"Avvio misura {Sij} per salvataggio...")
        try:
            # --- INIZIO CORREZIONE ---

            # AVVERTENZA: La tua classe VNA in __init__ configura 'Trc1'
            # per 'S21' in modo fisso. get_S_parameters() legge 'Trc1'.
            # Questo significa che misurerà SEMPRE S21,
            # indipendentemente da cosa passi all'argomento 'Sij'.
            if Sij != "S21" and Sij != "'S21'":
                print(f"ATTENZIONE: Il VNA è configurato per S21 (in __init__), ma è stato richiesto {Sij}.")
                print("Verranno salvati i dati S21.")

            # 1. Ottieni i dati S-parameter (Reale, Immaginario)
            # SOSTITUITO: data_dict = self.read_data(Sij)
            real_data, imag_data = self.get_S_parameters()
            
            # 2. Ottieni i dati di frequenza (Asse X)
            # SOSTITUITO: freq_data = self.read_frequency_data()
            freq_data = self.get_freq()
            
            # --- FINE CORREZIONE ---

            # 3. Controlla la directory di salvataggio (da Data.save_txt)
            save_dir = "../data"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
                print(f"Creata directory mancante: {save_dir}")

            # 4. Istanzia la classe Data con i tre vettori
            # x = Frequenza, y = Reale, z = Immaginario
            dati_misura = Data(x=freq_data, y=real_data, z=imag_data)
            
            # 5. Prepara un commento/header
            header = (
                f"Dati VNA {Sij}\n"
                f"Strumento: {self._VNA.query('*IDN?').strip()}\n"
                f"Punti: {len(freq_data)}\n"
                f"Colonne: Frequenza (Hz), Reale, Immaginario"
            )
            
            # 6. Usa il metodo .save_txt() della classe Data
            if dati_misura.save_txt(nome=filename, commento=header):
                print(f"Dati salvati con successo in: {save_dir}/{filename}.txt")
            else:
                print("Salvataggio fallito.")
                
        except Exception as e:
            print(f"ERRORE durante il salvataggio dei dati: {e}")
