from machine import Pin
import time

def validate_bits(bits):
    if not set(bits).issubset({'0', '1'}):
        raise ValueError("La chaine doit ne contenir que '0' et '1'.")
    return bits

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

def bytes_from_bits(bits):
    bits = validate_bits(bits)
    n = (len(bits) // 8) * 8
    bits = bits[:n]
    return bytes([int(bits[i:i+8], 2) for i in range(0, n, 8)])

RO = Pin(16, Pin.IN)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)
DE.value(0)                
RE.value(0)              

DEMI_BIT_US = 50000           
SPS = 10                     
PERIODE = DEMI_BIT_US // SPS  
def lire_signal(debut):
    signal = []
    repos = 0
    k = 0
    while repos < 4 * SPS:               
        instant = time.ticks_add(debut, k * PERIODE + PERIODE // 2)
        while time.ticks_diff(instant, time.ticks_us()) > 0:
            pass                          
        v = RO.value()
        signal.append(v)
        if v == 1:
            repos = repos + 1
        else:
            repos = 0
        k = k + 1
    return signal

def demi_bits_depuis_signal(signal):
    m = ""
    for s in range(0, len(signal) - SPS + 1, SPS):
        moy = sum(signal[s:s+SPS]) / SPS
        if moy >= 0.5:
            m = m + "1"
        else:
            m = m + "0"
    return m

def decoder_trame(signal):
    m = demi_bits_depuis_signal(signal)
    mbits = ""
    for i in range(0, len(m) - 1, 2):
        if m[i:i+2] == "10" or m[i:i+2] == "01":
            mbits = mbits + m[i:i+2]
        else:
            break
    bits = manchester_decode(mbits)                
    if len(bits) < 9 or bits[0] != "0":
        raise ValueError("Bit de synchro absent")
    return bytes_from_bits(bits[1:]).decode()     

print("En attente de trame...")
while True:
    while RO.value() == 1:                        
        pass
    signal = lire_signal(time.ticks_us())
    try:
        texte = decoder_trame(signal)
    except ValueError:
        print("Trame invalide")
        continue
    if texte.startswith("<") and texte.endswith(">"):
        print("Trame recue :", texte)
    else:
        print("Trame incomplete :", texte)
