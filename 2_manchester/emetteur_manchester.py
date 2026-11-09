from machine import Pin
import time


def validate_bits(bits):
    if not set(bits).issubset({'0', '1'}):
        raise ValueError("La chaine doit ne contenir que '0' et '1'.")
    return bits

def ascii_bytes(text):
    for c in text:
        if ord(c) > 127:
            raise ValueError("Caractere non-ASCII : " + c)
    return text.encode()

def bits_from_bytes(data):
    return ''.join(f'{b:08b}' for b in data)

def manchester_encode(bits):
    bits = validate_bits(bits)
    m = ""
    for b in bits:
        if b == "1":
            m = m + "10"
        else:
            m = m + "01"
    return m


DI = Pin(17, Pin.OUT)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)
RE.value(1)                 
DE.value(0)                   

STATION = "S01"
DEMI_BIT_US = 50000           

def envoyer_trame(texte):
    bits = bits_from_bytes(ascii_bytes(texte))    
    mbits = manchester_encode("0" + bits)         
    DE.value(1)                                   
    DI.value(1)                                    
    time.sleep_us(6 * DEMI_BIT_US)
    debut = time.ticks_us()
    for k in range(len(mbits)):                    
        DI.value(int(mbits[k]))
        instant = time.ticks_add(debut, (k + 1) * DEMI_BIT_US)
        while time.ticks_diff(instant, time.ticks_us()) > 0:
            pass                                   
    DI.value(1)                                    
    time.sleep_us(4 * DEMI_BIT_US)
    DE.value(0)                                   

while True:
    msg = input("Message a envoyer (ex: OK) : ")
    trame = "<" + STATION + ":" + msg + ">"
    print("Envoi de", trame)
    envoyer_trame(trame)
    print("Envoye !")
