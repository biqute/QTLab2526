import sys 
sys.path.append("../classes")
from LO import LO
import time

myLO1 = LO("COM11")
myLO2 = LO("COM12")
delta = 0
myLO1.freq = 1e8 + delta
myLO2.freq = 1e8

print(myLO1.freq)
print(myLO2.freq)
 
time.sleep(2)
myLO1.turn_on()
myLO2.turn_on()

#myLO1.turn_off()
myLO2.turn_off()



