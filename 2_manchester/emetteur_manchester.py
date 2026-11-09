from machine import Pin
import time

def validate_bits(bits):
    if not set(bits).issubset({'0', '1'}):
        raise ValueError("La chaine doit ne contenir que '0' et '1'.")
    return bits

def bits_from_bytes(data):
    return ''.join(f'{b:08b}' for b in data)

def bytes_from_bits(bits):
    bits = validate_bits(bits)
    n = (len(bits) // 8) * 8
    bits = bits[:n]
    return bytes([int(bits[i:i+8], 2) for i in range(0, n, 8)])

def ascii_bytes(text):
    for c in text:
        if ord(c) > 127:
            raise ValueError("Caractere non-ASCII : " + c)
    return text.encode()

def manchester_encode(bits):
    bits = validate_bits(bits)
    m = ""
    for b in bits:
        if b == "1":
            m = m + "10"
        else:
            m = m + "01"
    return m

def manchester_decode(mbits):
    mbits = validate_bits(mbits)
    if len(mbits) % 2 != 0:
        raise ValueError("Longueur impaire")
    bits = ""
    for i in range(0, len(mbits), 2):
        paire = mbits[i:i+2]
        if paire == "10":
            bits = bits + "1"
        elif paire == "01":
            bits = bits + "0"
        else:
            raise ValueError("Paire invalide : " + paire)
    return bits

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
