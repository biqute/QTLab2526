import sys; sys.path.append("../classes")
from LO import LO
import time

myLO1 = LO("COM11")
myLO2 = LO("COM12")

myLO1.freq = 5e9
myLO2.freq = 5.1e9

print(myLO1.freq)
print(myLO2.freq)

#myLO1.turn_off()
time.sleep(2)
myLO1.turn_on()
myLO2.turn_on()

