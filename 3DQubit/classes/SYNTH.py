import time
import serial

class class_SYNTH: # Removed (serial.Serial) to prevent double instantiation
    debug = True
    debug_prefix = ""

    def __init__(self, name, baudrate=9600):
        # Cleanly initialize a single serial connection instance
        self._LO = serial.Serial(name, baudrate=baudrate, timeout=1.0)  
        self._LO.flushInput() 
        self._LO.flushOutput()
        if not self._LO.is_open: 
            raise Exception("Connection failed.")

    def write(self, unterminated_command):
        # Valon accepts \r, \n or \r\n. Using \r\n is safe.
        command_utf8 = (unterminated_command + "\r\n").encode(encoding="utf-8")
        self._LO.write(command_utf8)

        if self.debug: 
            print(f"{self.debug_prefix}[WRITE]: {unterminated_command}")

    def query(self, unterminated_command):    
        command_utf8 = (unterminated_command + "\r\n").encode(encoding="utf-8")
        self._LO.write(command_utf8)
        
        # FIX 1: decode using "latin-1" so noisy startup bytes like 0xfe will never crash your code
        string = self._LO.readline().decode("latin-1").strip()

        # FIX 2: Handle the Valon command echo safely
        # If the device parrot-echoes the command, read the NEXT line to grab the real answer
        if string == unterminated_command:
            string = self._LO.readline().decode("latin-1").strip()

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
        # Convert Hz to MHz for Valon processing (e.g., 2e9 Hz -> 2000.0 MHz)
        f_mhz = f_hz / 1000000.0 
        
        self.write(f"FREQ {f_mhz}")
        time.sleep(0.05) # Small delay gives the synthesizer phase-locked loop time to lock
        self.freq = f_hz

        # Verifying frequency response string safely
        risposta = self.query("FREQ")
        print(f"Verifica frequenza: {risposta}")            

    def set_pow(self, pow_dbm):
        """Set power in dBm"""
        self.write(f"PWR {pow_dbm}")
        time.sleep(0.01)
        self.pow = pow_dbm