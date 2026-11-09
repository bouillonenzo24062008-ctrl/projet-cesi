from machine import Pin
import time

# ================= Fonctions du cours (Workshop 6) =================
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

# ================= Station emettrice =================
DI = Pin(17, Pin.OUT)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)
RE.value(1)                   # l'emetteur n'ecoute pas
DE.value(0)                   # au repos, la station lache la ligne

STATION = "S01"
DEMI_BIT_US = 50000           # duree d'un demi-bit en microsecondes (50 ms, 1 bit = 100 ms)

def envoyer_trame(texte):
    bits = bits_from_bytes(ascii_bytes(texte))     # texte -> ASCII -> bits
    mbits = manchester_encode("0" + bits)          # bit de synchro "0" + Manchester
    DE.value(1)                                    # on prend la ligne
    DI.value(1)                                    # repos
    time.sleep_us(6 * DEMI_BIT_US)
    debut = time.ticks_us()
    for k in range(len(mbits)):                    # un demi-bit toutes les 50 ms
        DI.value(int(mbits[k]))
        instant = time.ticks_add(debut, (k + 1) * DEMI_BIT_US)
        while time.ticks_diff(instant, time.ticks_us()) > 0:
            pass                                   # on attend la fin du demi-bit
    DI.value(1)                                    # retour au repos
    time.sleep_us(4 * DEMI_BIT_US)
    DE.value(0)                                    # on relache la ligne

while True:
    msg = input("Message a envoyer (ex: OK) : ")
    trame = "<" + STATION + ":" + msg + ">"
    print("Envoi de", trame)
    envoyer_trame(trame)
    print("Envoye !")
