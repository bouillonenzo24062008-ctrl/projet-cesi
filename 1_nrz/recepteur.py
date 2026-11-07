from machine import Pin
import time

RO = Pin(16, Pin.IN)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)

DE.value(0)   
RE.value(0)  

while True:
    print("Niveau NRZ recu :", RO.value())
    time.sleep(0.2)
