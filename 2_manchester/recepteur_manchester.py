from machine import Pin
import time

RO = Pin(16, Pin.IN)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)
DE.value(0)
RE.value(0)

T_US = 100000           
DEMI = T_US // 2
QUART = T_US // 4

def attendre_front(niveau, t_fin):
    while time.ticks_diff(t_fin, time.ticks_us()) > 0:
        if RO.value() != niveau:
            return time.ticks_us()
    return None

def recevoir_bits():
    while RO.value() == 1:         
        pass
    debut_bit = time.ticks_us()
    bits = []
    while True:
        milieu = time.ticks_add(debut_bit, DEMI)
        ouverture = time.ticks_add(milieu, -QUART)
        fermeture = time.ticks_add(milieu, QUART)
        while time.ticks_diff(ouverture, time.ticks_us()) > 0:
            pass                 
        niveau = RO.value()       
        t_front = attendre_front(niveau, fermeture)
        if t_front is None:
            break                   
        bits.append(niveau)       
        debut_bit = time.ticks_add(t_front, DEMI)   
    return bits

def bits_vers_texte(bits):
    texte = ""
    for k in range(0, len(bits) - 7, 8):
        o = 0
        for b in bits[k:k + 8]:
            o = (o << 1) | b
        texte += chr(o)
    return texte

print("En attente de trame...")
while True:
    bits = recevoir_bits()
    if len(bits) < 9 or bits[0] != 0:
        print("Trame invalide")
        continue
    texte = bits_vers_texte(bits[1:])     
    if texte.startswith("<") and texte.endswith(">"):
        print("Trame recue :", texte)
    else:
        print("Trame incomplete :", texte)
