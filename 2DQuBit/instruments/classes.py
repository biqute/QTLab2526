import numpy as np
import pyvisa
import re


# ----------------------------- WAVEFORM GENERATOR ---------------------------------

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

    def manual_trig(self):
        self._SDG.write("C1:BTWV MTRIG")
        
    def set_formwave(self, ch, wtp, index = 0) : #probably pass wtp as string
        if wtp == 'arb' or wtp == 'ARB':
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

    def set_burst(self, ch):
        self._SDG.write(f"C{ch}:BTWV CARR,WVTP,SINE")
        print(self._SDG.query(f"*OPC?"))

    def burst_on(self):
        self._SDG.write(f"C1:BTWV STATE,OFF")
        print(self._SDG.query(f"*OPC?"))
        self._SDG.write(f"C1:BTWV TRSR,MAN")
        self._SDG.write(f"C1:BTWV GATE_NCYC,NCYC")
        self._SDG.write(f"C1:BTWV TIME,1")
        self._SDG.write(f"C1:BTWV PRD,1000S")
        self._SDG.write(f"C1:BTWV COUNT,1")
        self._SDG.write(f"C1:BTWV TRMD,OFF")    #....
        self._SDG.write(f"C1:BTWV DLAY,0S")
        self._SDG.write(f"C1:BTWV STATE,ON")
        print(f"Modalità Burst PARAMETERS: {self._SDG.query('C1:BTWV?')}")
        self._SDG.write(f"C1:BTWV MTRIG")
        print(self._SDG.query(f"*OPC?"))

    def modulation(self,ch, f_m):
        """Turn ON and OFF the modulation"""
        # AM = amplitude modulation, MDSP = modulation wave shape, ARB = arbitrary
        SDG.turn_mod_on(self, ch)
        self._SDG.write(f"C1:MDWV AM")
        self._SDG.write(f"C1:MDWV AM,SRC,INT")
        self._SDG.write(f"C1:MDWV AM,FRQ,{f_m}")
        self._SDG.write(f"C1:MDWV MDSP,ARB,INDEX,19")
        print(self._SDG.query(f"*OPC?"))
    

    def gaussian_pulse(self, ch, f, amp, phase, off, f_m) :
        SDG.set_all(self, ch, f, amp, phase, off)
        SDG.set_formwave(self, ch, 'SINE')
        SDG.modulation(self, ch, f_m)
       
    def singleshot(self, ch, f, amp, phase, off, f_m ):
        SDG.gaussian_pulse(self, ch, f, amp, phase, off, f_m)
        a =self._SDG.query(f'C{ch}:MDWV?')
        parts = a.split(',')
        if parts[1] != 'OFF': SDG.turn_mod_off(self, ch)
        SDG.set_burst(self, ch)
        SDG.burst_on(self)



    
        

    
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
    
        

    def set_trigger(self, source_channel=2, coupling='DC'):
        ch_name = f'CH{source_channel}'
        self._TDS.write(f'TRIGger:A:TYPe PULSE')
        self._TDS.write(f'TRIGger:A:PULse:SOUrce {ch_name}')
        self._TDS.write(f'TRIGger:A:EDGE:COUPling {coupling.upper()}')
        self._TDS.write(f'TRIGger:A:MODe NORMal')

    #C:\Users\oper\labQT\Lab2025\2DQubit\QTLab2526\2DQuBit\instruments\speranza.txt'
    
    def set_trigger_pulse_stable(self, source_channel=2, pulse_level_V=0.5, pulse_width_s=20e-6, pulse_condition='LESS', coupling='DC'):
        """
        Imposta il Canale specificato (CH2) come trigger stabile di tipo PULSE (Impulso).
        
        :param source_channel: Canale sorgente (es. 2).
        :param pulse_level_V: Livello di tensione (in Volt) a cui scatta il trigger.
        :param pulse_width_s: La larghezza di riferimento dell'impulso che stiamo cercando.
        :param pulse_condition: Condizione temporale per il trigger ('LESS', 'MORE', 'EQUAL', 'UNEQUAL').
        :param coupling: Accoppiamento del trigger ('DC', 'AC').
        """
        ch_name = f'CH{source_channel}'
        
        # 1. Imposta il Tipo di Trigger su PULSE
        self._TDS.write(f'TRIGger:A:TYPe PULSE')
        
        # 2. Imposta la Sorgente del Trigger
        self._TDS.write(f'TRIGger:A:PULse:SOUrce {ch_name}')
        
        # 3. Imposta il Livello di Tensione (CRUCIALE)
        # Il trigger scatta solo quando l'impulso supera questo livello.
        # Sintassi SCPI: TRIGger:A:LEVel <livello>
        self._TDS.write(f'TRIGger:A:LEVel {pulse_level_V}')
        
        # 4. Imposta l'Accoppiamento (Coupling)
        # Sintassi SCPI: TRIGger:A:PULse:COUPling DC (Nota il cambio di sottosistema da EDGE a PULSE)
        self._TDS.write(f'TRIGger:A:PULse:COUPling {coupling.upper()}')
        
        # 5. Definisci la Condizione di Durata dell'Impulso (CRUCIALE per PULSE)
        # Un trigger di impulso richiede una condizione temporale (es. impulso più largo di X ns)
        # Sintassi SCPI: TRIGger:A:PULse:WIDth:CONDition LESS
        self._TDS.write(f'TRIGger:A:PULse:WIDth:CONDition {pulse_condition.upper()}')
        
        # 6. Definisci la Larghezza di Riferimento dell'Impulso
        # Se stiamo cercando un impulso di 20 us, impostiamo quel valore.
        # Sintassi SCPI: TRIGger:A:PULse:WIDth:TIME <tempo>
        self._TDS.write(f'TRIGger:A:PULse:WIDth:TIME {pulse_width_s}')
        
        # 7. Modalità Normale (attende un trigger valido)
        self._TDS.write(f'TRIGger:A:MODe NORMal')
        
        print(f"Trigger PULSE impostato su {ch_name}. Livello: {pulse_level_V}V, Condizione: {pulse_condition.upper()} {pulse_width_s}s.")


    def set_acquire_state(self, state):
    
        if isinstance(state, str):
            state = state.upper()
        if state not in ['OFF','ON','RUN','STOP']:
            raise ValueError("State must be 'OFF', 'ON', 'RUN', or 'STOP'")
        self._TDS.write(f"ACQ:STATE {state}")
