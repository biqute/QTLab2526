import sys 
sys.path.append("../classes")
from LO import LO
import time

myLO1 = LO("COM11")
myLO2 = LO("COM12")
delta = 1.7e3
myLO1.freq = 5e9 
myLO2.freq = myLO1.freq + delta

print(myLO1.freq)
print(myLO2.freq)
 
time.sleep(2)
myLO1.turn_on()
myLO2.turn_on()

#myLO1.turn_off()
#myLO2.turn_off()