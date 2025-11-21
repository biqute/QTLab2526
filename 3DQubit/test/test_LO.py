import sys; sys.path.append("../classes")
from LO import LO
import time

myLO = LO("COM12")
myLO.freq = 5e9

print(myLO.freq/1e12)

myLO.turn_off()
time.sleep(2)
myLO.turn_on()

"""
import pyvisa

rm = pyvisa.ResourceManager()
myLO = rm.open_resource('ASRL4::INSTR')

# myLO.write_termination = "\r" # chr(13)
# myLO.read_termination = "\r" # chr(13)
myLO.baud_rate = 115200
myLO.data_bits = 8
myLO.stop_bits = pyvisa.constants.StopBits.one
myLO.parity = pyvisa.constants.Parity.none
myLO.flow_control = pyvisa.constants.VI_ASRL_FLOW_NONE
myLO.timeout = 10e3

freq = 5e9 * 1000 # mHz
id = myLO.query("*IDN?")
print(id)
myLO.write(f'FREQ 4GHz')
myLO.write('OUTP:STAT ON')
print(myLO.query("FREQ?"))
#myLO.write("FREQ 4GHz")
"""


"""
import serial
import time

class QuickSyn(serial.Serial):
    
    def __init__(self, name):
        self.ser = serial.Serial(name)  # open serial port
        # Clear the input buffer to ensure there are no pending commands
        self.ser.flushInput()
        #check
        if not self.ser.is_open:
            raise ValueError('Connection failed. Check the port name and the device.')
    
    def set_frequency(self, frequency, order="GHz"):
        if order not in ["GHz", "MHz", "KHz", "mlHz"]:
            raise ValueError('Order should be one of: GHz, MHz, KHz, mlHz.')   
        
        self.__write(f'FREQ {float(frequency)}{order}')
        # Set output state to ON
        time.sleep(0.5)
        self.__write('OUTP:STAT ON')
    
    def get_frequency(self, order="GHz"):
        if order not in ["GHz", "MHz", "KHz", "Hz", "mlHz"]:
            raise ValueError('Order should be one of: GHz, MHz, KHz, Hz, mlHz.')   
        
        self.__write('FREQ?')
        frequency = self.ser.readline().decode('utf-8').strip() # default order is mlHz
        
        if order == "GHz":
            frequency = float(frequency) / 1e12
        elif order == "MHz":
            frequency = float(frequency) / 1e9
        elif order == "kHz":
            frequency = float(frequency) / 1e6
        elif order == "Hz":
            frequency = float(frequency) / 1e3
        else:
            frequency = float(frequency)
                
        return frequency
        
    def __write(self, command_str):
        command_str += '\r\n'
        encoded_command = command_str.encode(encoding='utf-8')
        self.ser.write(encoded_command)
        
    def close_conncetion(self):
        #turn off the output
        self.__write('OUTP:STAT OFF')
        # Close the serial port
        self.ser.close()
        # Check if the port is closed
        if self.ser.is_open:
            raise ValueError('Connection failed to close. Check the port name and the device.')
        

# syn = QuickSyn("COM4")
# syn.set_frequency(1, "GHz")
# print(syn.get_frequency("GHz"))
"""


'''
def freq_to_hex(freq):
    milliHz = int(freq * 1000)
    str = hex(milliHz)[2:]

    if len(str) % 2 == 1:
        str = f"0{str}"
    
    spaced_str = ""

    for i, c in enumerate(str):
        if i % 2 == 1:
            spaced_str = f"{spaced_str}{c} "
        else:
            spaced_str = f"{spaced_str}{c}"

    spaced_str = spaced_str[:-1]

    return list(map(lambda s: int(s, 16), spaced_str.split(" ")))

rm = pyvisa.ResourceManager()
devlist = rm.list_resources()
print(devlist)
myLO = rm.open_resource('ASRL4::INSTR')

freq = 5e9 # Hz

data = [0x0C] + freq_to_hex(freq)
print(data)

myLO.write_raw(list(map(lambda x: x.to_bytes(), data)))
'''