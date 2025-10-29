import pyvisa
import numpy as np

VNA_IP = "193.206.156.99"

rm = pyvisa.ResourceManager()
vna = rm.open_resource(f"TCPIP0::{VNA_IP}::inst0::INSTR")

print("Connected to:", vna.query("*IDN?"))

