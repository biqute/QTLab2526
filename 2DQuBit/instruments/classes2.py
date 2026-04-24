from os import name
import numpy as np
import pyvisa
import re
import warnings
import matplotlib.pyplot as plt
import sys
import time
import serial

# ----------------------------- WAVEFORM GENERATOR ---------------------------------
def gaussian_sine(x, dict_par):
        A = dict_par['A']
        mu = dict_par['mu']
        sigma = dict_par['sig']
        f = dict_par['f']
        gauss = A * np.exp(-((x - mu)**2) / (2 * sigma**2))
        sine = np.sin(2 * np.pi * f * x)
        y = gauss * sine
        return y

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

        
    def set_samp(self, srate):
        self._SDG.write(f"C1:SRATE VALUE,{srate}") 
    
    def set_formwave(self, wtp):
        self._SDG.write(f'C1:BSWV WVTP,'+wtp)

    def set_arb_formwave(self, ch, wtp, index = 0) : #probably pass wtp as string
        if wtp.islower() == True : wtp = wtp.upper()
        if wtp == 'ARB':
            self._SDG.write(f'C{ch}'+":BSWV WVTP,ARB")
            self._SDG.write(f'C{ch}:ARbWaVe INDEX,{index}')
        else: 
            self._SDG.write(f'C{ch}'+":BSWV WVTP,"+wtp)
    
    def set_all(self, ch, f, amp, phase, off) :

        self._SDG.write(f'C{ch}'+f":BSWV FRQ,{f},"+f'AMP,{amp},'+f'PHSE,{phase},'+f'OFST,{off}' )

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
        
    def turn_mod_off(self, ch):
        self._SDG.write(f"C{ch}:MDWV STATE,OFF")

    def turn_mod_on(self, ch):
        self._SDG.write(f"C{ch}:MDWV STATE,ON")

    def upload_waveform(self, dict_par):
        interval = [-dict_par['n_sigma']*dict_par['sig'], +dict_par['n_sigma']*dict_par['sig']]
        duration = interval[1] - interval[0]
        samples_per_second = 2.4e9
        if duration * samples_per_second > 2400:
            samples_per_second = 2400 / duration
        samples = int(duration * samples_per_second)
        array = np.zeros(samples, dtype=np.int16)
        N = 15
        cropped = 0
        for i in range(0,samples):
            f = gaussian_sine(interval[0] + i / samples_per_second, dict_par=dict_par)
            n = int(round((2**N)*f))
            if n > (2**N - 1): 
                n = 2**N - 1
                cropped += 1
            if n < -2**N: 
                n = -2**N
                cropped += 1
            array[i] = n 
            if cropped > 0: 
                warnings.warn(f"The function 'func' was cropped to the range [-1, +1], for a total of {cropped} cropped samples.", stacklevel=2)


        array[0] = 0
        array[-1] = 0

        self._SDG.write_binary_values(f"C1:WVDT WVNM,{dict_par['name']},LENGTH,{samples},WAVEDATA,", array, datatype="h", is_big_endian=False, header_fmt='empty')
        self._SDG.write(f"C1:ARWV NAME,{dict_par['name']}")
        
        arb_freq = 1/duration
        self._SDG.write(f"C1:BSWV FRQ,{arb_freq}")

        if dict_par['plot'] == True :
            plt.figure(figsize=(10, 5))
            plt.plot(np.linspace(interval[0], interval[1], samples), array)
            plt.show() 
            print("duration = ", duration)
            print("samples", samples)
            print("frequenza del segnale gaussiano = ", arb_freq)
        
    def burst_mode(self, dict_par):
        self._SDG.write("C1:OUTP OFF")
        self._SDG.write("C1:BTWV MODE,NCYC") 
        self._SDG.write(f"C1:BTWV NCYC,{dict_par['N_cycles']}") 
        self._SDG.write(f"C1:BTWV TIME,1")
        self._SDG.write(f"C1:BTWV PRD,3")
        self._SDG.write("C1:BTWV TRSR,MAN")
        self._SDG.write("C1:BTWV STATE,ON")
        self._SDG.write("C1:BTWV ILVL,0V")
        print(self._SDG.query("*OPC?"))
    
    def manual_trig(self):
        
        self._SDG.write("C1:OUTP ON") 
        self._SDG.write("C1:BTWV MTRIG")
        a=self._SDG.query("*OPC?")
        return a
    
    def stop_burst(self):
        self._SDG.write("C1:BTWV STATE,OFF")
    
    def stop_all(self):
        self._SDG.write("C1:OUTP OFF") 
        self._SDG.write("C1:BTWV STATE,OFF")

    def prepare(self):
        self._SDG.write("C1:OUTP OFF") 
        self._SDG.write("C1:BTWV STATE,OFF")

    
# ----------------------------- VECTOR NETWORK ANALYSER ---------------------------------

class VNA():
    def __init__(self, ip_address) :
        
        rm = pyvisa.ResourceManager ()
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
    
    def get_data(self, Sij="S21"):
        
        self._VNA.write(f"CALC:PAR:DEF {Sij}")
        self._VNA.write("FORM ASC")
        self._VNA.write("INIT:CONT OFF") # Disabilita lo sweep continuo
        self._VNA.write("INIT:IMM")      # Fa partire uno sweep singolo
        self._VNA.query("*OPC?")

        #self._VNA.wait
        # Dati formattati (Reale, Immaginario)
        data_string = self._VNA.query("CALC:DATA:SDATA?")
        data = np.array(list(map(float, data_string.split(","))))
        
        real = np.array(data[0::2])
        imag = np.array(data[1::2])
        self._VNA.write("INIT:CONT ON")

        return real, imag
    

    def save_vna_data(self, filename, freqs, real, imag):

        # 1. Combiniamo Reale e Immaginario nel vettore complesso S21
        S21_complex = real + 1j * imag
        
        # 2. Estraiamo Ampiezza (signal) e Fase in radianti (phase)
        signal = np.abs(S21_complex)
        phase = np.angle(S21_complex)
        
        # 3. Salviamo i dati indicando esplicitamente le chiavi 'freq', 'signal' e 'phase'
        # Questo farà in modo che la funzione safe_load_npz del tuo script le riconosca subito.
        np.savez(filename, freq=freqs, signal=signal, phase=phase)
        
        print(f"File salvato con successo: {filename} ({len(freqs)} punti)")
        
        
        
    def save_vna_data2(self, filename, freqs, real, imag):
        import numpy as np # Assicurati che numpy sia importato

        # 1. Combiniamo Reale e Immaginario nel vettore complesso S21
        S21_complex = real + 1j * imag
        
        # 2. Estraiamo Ampiezza (signal) e Fase in radianti (phase)
        signal = np.abs(S21_complex)
        phase = np.angle(S21_complex)
        
        # 3. Creiamo l'array strutturato (Structured Array) esattamente come lo vuole il fit
        # Definiamo il tipo di dato (dtype) complesso con i nomi richiesti
        dt = np.dtype([('freq', '<f8'), 
                       ('signal', '<f8'), 
                       ('phase', '<f8'), 
                       ('error_signal', '<f8'), 
                       ('error_phase', '<f8')])
        
        # Creiamo un array vuoto con questa struttura, lungo quanto i nostri dati
        structured_data = np.zeros(len(freqs), dtype=dt)
        
        # Riempiamo l'array strutturato
        structured_data['freq'] = freqs
        structured_data['signal'] = signal
        structured_data['phase'] = phase
        # I campi 'error_signal' ed 'error_phase' rimangono a zero, 
        # dato che nel mock non calcoliamo l'errore punto per punto.
        
        # 4. Salviamo l'array strutturato in un file .npz usando un dizionario.
        # Spesso questi vecchi script si aspettano che la chiave sia '0' o 'arr_0'
        # Usare '0' nel dizionario simula il comportamento di default o specifico.
        np.savez(filename, **{'0': structured_data}) 
        
        print(f"File salvato con successo NEL NUOVO FORMATO STRUTTURATO: {filename} ({len(freqs)} punti)")

# - - - - - - - - - - - - - - - - - OSCILLOSCOPE - - - - - - - - - - - - - 

class TDS() :
    def __init__(self, address) :
        
        rm = pyvisa.ResourceManager()
        self._TDS = rm.open_resource("GPIB0::"+address+"::INSTR")  
        self._TDS.write("*CLS")

    def get_IDN(self):
        return self._TDS.query("*IDN?")

    def turn_on(self):
        self._TDS.write("ALIAS:STATE ON")
 
    def turn_off(self):
        self._TDS.write(":CHAN1:DISP OFF")
    
    def read_par (self, ch):
        a = self._TDS.query(f'CH{ch}?')
        return a
    
    def scale (self, ch, scale):
        self._TDS.write(f'CH{ch}:SCAle {scale}')

    def get_scale (self, ch):
        return float(self._TDS.query(f'CH{ch}:SCAle?'))
    
    def res(self, ch, res):
        if res == 50 or res == 1e6:
            self._TDS.write(f'CH{ch}:TER {res}')
        else: raise ValueError('The resistence must be 50  o 1M')

    def get_sample_rate(self):
        return self._TDS.query('HORizontal:MAIn:SAMPLERate?')

    def set_sample_rate(self, num):
        self._TDS.write(f'HORizontal:MAIn:SAMPLERate {num}')
   
    def set_hor_scale(self, y):
        self._TDS.write(f'HORizontal:MAIn:SCAle {y}')

    def prepare_for_trigger(self):
        #self._TDS.write("ACQ:STOPAFTER SEQUENCE") # Si ferma dopo un singolo evento         
        self._TDS.write("TRIGger:A:MODe NORM") # Modalità di trigger normale
        self._TDS.write("ACQ:STATE ON")        # Avvia l'ascolto del trigger
        self._TDS.write("ACQ:STATE RUN")        # Avvia l'ascolto del trigger
    
    

    def acquisition(self, ch, start, stop):
        h_sc = self._TDS.query("HOR:SCA?")
        Sr = self._TDS.query("HORizontal:MAIn:SAMPLERate?")
        v_sc = float(self._TDS.query(f'CH{ch}:SCAle?'))
        self._TDS.write(f'DAT:SOU CH{ch}')
        self._TDS.write(f'DAT:ENC ASCI')
        self._TDS.write(f'DAT:STAR {start}')
        self._TDS.write(f'DAT:STOP {stop}')
        data = self._TDS.query('CURV?')
        parts = data.split(',')
        data_array = np.array([float(parts[i]) for i in range (len(parts))])
        rescaled_data = data_array*4*v_sc/100
        result = dict(H_scale=float(h_sc), sample_rate = float(Sr), V_scale = float(v_sc), raw_data = data_array, data = rescaled_data)
        return result
    
    def plot_acquisition(self, mode):
        start, stop = 0, 500
        X = self.acquisition(1, start, stop)
        print(X['sample_rate'], len(X['data']))
        if mode == 1:
            Y = self.acquisition(2, start, stop)
        else: Y = None
        x = np.linspace(0, (stop-start)/X['sample_rate'], len(X['data']))
        z = np.zeros(len(x))
        fig, ax = plt.subplots(figsize=(10,5))
        plt.plot(x, X['data'], color = 'purple', label = 'I')
        if mode == 1:
            y = np.linspace(0, (stop-start)/Y['sample_rate'], len(Y['data']))
            plt.plot(y, Y['data'], color = 'orange', label = 'Q')
            plt.legend()
        plt.plot(x, z)
        plt.show()
        return X, Y

            

    def set_acquire_state2(self, state):
    
        if isinstance(state, str):
            state = state.upper()
        if state not in ['OFF','ON','RUN','STOP']:
            raise ValueError("State must be 'OFF', 'ON', 'RUN', or 'STOP'")
        self._TDS.write(f"ACQ:STATE {state}")
   
    def get_acquire_state(self):
        return self._TDS.query("ACQ:MAXS?")
    
    def acquire_all(self):
        return self._TDS.query("ACQ?")
    
    def acquire_trig(self):
        return self._TDS.query("TRIG?")


# ----------------------------- LOCAL OSCILLATOR ---------------------------------
class LO():

    debug = True
    debug_prefix = ""

    def __init__(self, name):
        self._LO = serial.Serial(name)  # open serial port
        self._LO.flushInput() # Clear the input buffer to ensure there are no pending commands
        

        if not self._LO.is_open: raise Exception("Connection failed.")


    def write(self, unterminated_command):
        command_utf8 = (unterminated_command + "\r\n").encode(encoding="utf-8")
        self._LO.write(command_utf8)

        if self.debug: print(f"{self.debug_prefix}[{unterminated_command}]")

    def query(self, unterminated_command):    
        command_utf8 = (unterminated_command + "\r\n").encode(encoding="utf-8")
        self._LO.write(command_utf8)
        string = self._LO.readline().decode("utf-8").strip()

        if self.debug: print(f"{self.debug_prefix}[{unterminated_command}] {string}")

        return string
    
    def get_IDN(self):
        return self.query("*IDN?")
    
    def get_stat(self):
        return self.query("OUTP:STAT?")
    
    def get_source_stat(self):
        return self.query("SOUR:ROSC:SEL?")

    def turn_on(self):
        self.write("OUTP:STAT ON") # turn on the output
    
    def turn_off(self):
        self.write("OUTP:STAT OFF") # turn off the output
    
    def get_pot(self):
        return self.query("POW?")
    
    def get_freq(self):
        return self.query("FREQ?")

    def set_freq(self, f):
        """Set synthetized frequency in Hz"""
        f_millis = f * 1000 # f in mHz
        self.write(f"FREQ {f_millis}mlHz")
        time.sleep(0.005)
        #self.write('OUTP:STAT ON')
        self.freq = f

        print(type(self.query("FREQ?")), self.query("FREQ?"))              

        if int(self.query("FREQ?")) != f_millis: 
            raise Exception(f"Could not set 'freq' to {f}.")  
    def set_pow(self, pow):
        self.write(f"POW {pow}dBm")
        time.sleep(0.005)
        self.pow = pow 

#------------------function to acquire a singleshot------------------------------
def acquire_singleshot(dict_par):
    # 1 Caricare la waveform sul generatore
    my_sdg = SDG('193.206.156.10')
    my_sdg.upload_waveform(dict_par)
    # 2 Configurare SDG in modalità burst
    my_sdg.burst_mode(dict_par)
    # 3 Preparare l'oscilloscopio per il trigger
    tds = TDS('3')
    tds.set_hor_scale(dict_par['sig'])
    tds.prepare_for_trigger()
    # 4 Inviare l'impulso dal generatore
    time.sleep(1) # Aspetta un po' prima di inviare il trigger per assicurarsi che l'oscilloscopio sia pronto
    my_sdg.manual_trig()
   # 5spengi sdg
    my_sdg.stop_all()
    # 6 Acquisizione dati
    X, Y = tds.plot_acquisition(0)
   
def acquire_IQ(dict_par):
    # 1 Caricare la waveform sul generatore
    my_sdg = SDG('193.206.156.10')
    my_sdg.upload_waveform(dict_par)
    time.sleep(5) 
    # 2 Configurare SDG in modalità burst
    my_sdg.burst_mode(dict_par)
    # 3 Preparare l'oscilloscopio per il trigger
    tds = TDS('3')
    tds.set_hor_scale(dict_par['sig'])
    time.sleep(5)
    tds.prepare_for_trigger()
    time.sleep(5)
    # 4 Inviare l'impulso dal generatore
    my_sdg.manual_trig()
    time.sleep(10*dict_par['sig']) # Aspetta un po' prima di inviare il trigger per assicurarsi che l'oscilloscopio sia pronto
    # 5spengi tutto
    tds.set_acquire_state2('OFF')
    my_sdg.stop_all()
    # 6 Acquisizione dati
     # Aspetta un po' prima di inviare il trigger per assicurarsi che l'oscilloscopio sia pronto
    I, Q = tds.plot_acquisition(1)



# SIMULATORE DI VNA PER TESTARE IL CODICE DI ACQUISIZIONE E ANALISI DEI DATI SENZA AVERE IL VNA A DISPOSIZIONE
class MockVNA:
    def __init__(self, f_center=4.58, span=0.01, num_points=2000):
        # Imposta le frequenze che il VNA scansionerà (in GHz)
        self.freqs = np.linspace(f_center - span/2, f_center + span/2, num_points)
        
        # Parametri fisici del tuo risonatore superconduttore
        self.f0 = f_center      # Frequenza di risonanza (GHz)
        self.Ql = 15000         # Fattore di qualità caricato (Loaded Q)
        self.Qc = 18000         # Fattore di qualità di accoppiamento (Coupling Q)
        
        # Imperfezioni del setup nel criostato
        self.cable_delay = 15e-9 # Ritardo dei cavi (15 ns)
        self.noise_level = 0.002 # Livello di rumore bianco

    def get_frequencies(self):
        """Restituisce l'array delle frequenze scansionate."""
        return self.freqs

    def get_data(self, param="S21"):
        """Restituisce le componenti Reale e Immaginaria del segnale."""
        if param != "S21":
            raise ValueError("Errore: il simulatore supporta solo S21.")

        # 1. Calcolo della risposta ideale del risonatore (Notch)
        dx = (self.freqs - self.f0) / self.f0
        S21_ideal = 1 - (self.Ql / self.Qc) / (1 + 2j * self.Ql * dx)

        # 2. Aggiunta della rotazione di fase dovuta ai cavi lunghi
        cable_phase = np.exp(-2j * np.pi * self.freqs * 1e9 * self.cable_delay)
        
        # 3. Aggiunta del rumore di misura
        noise = np.random.normal(0, self.noise_level, len(self.freqs)) + \
                1j * np.random.normal(0, self.noise_level, len(self.freqs))

        # Segnale finale combinato
        S21_measured = (S21_ideal + noise) * cable_phase

        return np.real(S21_measured), np.imag(S21_measured)
    
    def save_vna_data(self, filename, freqs, real, imag):

        # 1. Combiniamo Reale e Immaginario nel vettore complesso S21
        S21_complex = real + 1j * imag
        
        # 2. Estraiamo Ampiezza (signal) e Fase in radianti (phase)
        signal = np.abs(S21_complex)
        phase = np.angle(S21_complex)
        
        # 3. Salviamo i dati indicando esplicitamente le chiavi 'freq', 'signal' e 'phase'
        # Questo farà in modo che la funzione safe_load_npz del tuo script le riconosca subito.
        np.savez(filename, freq=freqs, signal=signal, phase=phase)
        
        print(f"File salvato con successo: {filename} ({len(freqs)} punti)")


    def save_vna_data2(self, filename, freqs, real, imag):
        import numpy as np # Assicurati che numpy sia importato

        # 1. Combiniamo Reale e Immaginario nel vettore complesso S21
        S21_complex = real + 1j * imag
        
        # 2. Estraiamo Ampiezza (signal) e Fase in radianti (phase)
        signal = np.abs(S21_complex)
        phase = np.angle(S21_complex)
        
        # 3. Creiamo l'array strutturato (Structured Array) esattamente come lo vuole il fit
        # Definiamo il tipo di dato (dtype) complesso con i nomi richiesti
        dt = np.dtype([('freq', '<f8'), 
                       ('signal', '<f8'), 
                       ('phase', '<f8'), 
                       ('error_signal', '<f8'), 
                       ('error_phase', '<f8')])
        
        # Creiamo un array vuoto con questa struttura, lungo quanto i nostri dati
        structured_data = np.zeros(len(freqs), dtype=dt)
        
        # Riempiamo l'array strutturato
        structured_data['freq'] = freqs
        structured_data['signal'] = signal
        structured_data['phase'] = phase
        # I campi 'error_signal' ed 'error_phase' rimangono a zero, 
        # dato che nel mock non calcoliamo l'errore punto per punto.
        
        # 4. Salviamo l'array strutturato in un file .npz usando un dizionario.
        # Spesso questi vecchi script si aspettano che la chiave sia '0' o 'arr_0'
        # Usare '0' nel dizionario simula il comportamento di default o specifico.
        np.savez(filename, **{'0': structured_data}) 
        
        print(f"File salvato con successo NEL NUOVO FORMATO STRUTTURATO: {filename} ({len(freqs)} punti)")