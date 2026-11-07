from machine import Pin
import time

DI = Pin(17, Pin.OUT)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)

RE.value(1)   # l'émetteur n'écoute pas

while True:
    DE.value(1); DI.value(1); print("J'envoie 1")
    time.sleep(1)
    DE.value(1); DI.value(0); print("J'envoie 0")
    time.sleep(1)
    DE.value(0); print("Haute impedance")
    time.sleep(1)
