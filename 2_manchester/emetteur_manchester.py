from machine import Pin
import time

DI = Pin(17, Pin.OUT)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)
RE.value(1)
DE.value(0)          

STATION = "S01"
T_MS = 100               
DEMI = T_MS // 2

def envoyer_bit(b):
    DI.value(b)
    time.sleep_ms(DEMI)
    DI.value(1 - b)
    time.sleep_ms(DEMI)

def envoyer_trame(texte):
    DI.value(1)
    DE.value(1)                    
    time.sleep_ms(3 * T_MS)
    envoyer_bit(0)                  
    for c in texte:
        o = ord(c)
        for i in range(7, -1, -1): 
            envoyer_bit((o >> i) & 1)
    DI.value(1)
    time.sleep_ms(2 * T_MS)
    DE.value(0)                    

while True:
    msg = input("Message a envoyer (ex: OK) : ")
    trame = "<" + STATION + ":" + msg + ">"
    print("Envoi de", trame)
    envoyer_trame(trame)
    print("Envoye !")
