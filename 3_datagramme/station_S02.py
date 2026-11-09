from machine import Pin, I2C
import time, random, dht, sys, select

# ================= Fonctions du cours (Workshop 6) =================
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

def utf8_bytes(text):
    return text.encode('utf-8')

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

# ================= Configuration =================
STATION = "S02"          # <-- STATION 2 (sans capteur)
VIVRES = 80                   # niveau de vivres en % (modifiable : taper V=75)
MESSAGE = "OK"                # message d'etat (modifiable depuis la console)
EMETTEUR = False              # False : reception seule (mettre True pour qu'elle envoie aussi)
PERIODE_MS = 15000            # envoi automatique toutes les ~15 s
DEMI_BIT = 10                 # duree d'un demi-bit en ms (1 bit = 20 ms)
DEMI_BIT_US = DEMI_BIT * 1000 # meme duree, en microsecondes

DI = Pin(17, Pin.OUT)
RO = Pin(16, Pin.IN)
DE = Pin(25, Pin.OUT)
RE = Pin(26, Pin.OUT)
DE.value(0)                   # au repos, on lache la ligne
RE.value(0)                   # on ecoute en permanence
capteur = dht.DHT11(Pin(27))

# ================= Ecran LCD (I2C : SCL = GPIO 18, SDA = GPIO 19) =================
class EcranLCD:
    # pilote simple d'un ecran 16x2 avec module I2C (PCF8574)
    def __init__(self, i2c, adresse):
        self.i2c = i2c
        self.adresse = adresse
        time.sleep_ms(50)
        for i in range(3):              # sequence d'initialisation de l'ecran
            self.demi_octet(0x30, 0)
            time.sleep_ms(5)
        self.demi_octet(0x20, 0)        # passage en mode 4 bits
        self.commande(0x28)             # 2 lignes
        self.commande(0x0C)             # ecran allume, pas de curseur
        self.commande(0x06)             # ecriture de gauche a droite
        self.commande(0x01)             # effacer l'ecran
        time.sleep_ms(2)

    def envoyer(self, valeur):
        self.i2c.writeto(self.adresse, bytes([valeur | 0x08]))   # 0x08 = retroeclairage

    def demi_octet(self, valeur, rs):
        self.envoyer(valeur | rs | 0x04)     # impulsion sur la broche E de l'ecran
        self.envoyer(valeur | rs)

    def octet(self, valeur, rs):
        self.demi_octet(valeur & 0xF0, rs)
        self.demi_octet((valeur << 4) & 0xF0, rs)

    def commande(self, c):
        self.octet(c, 0)

    def ecrire_ligne(self, ligne, texte):
        texte = texte[:16]
        texte = texte + " " * (16 - len(texte))   # on complete a 16 caracteres
        if ligne == 0:
            self.commande(0x80)
        else:
            self.commande(0xC0)
        for c in texte:
            self.octet(ord(c), 1)

try:
    i2c = I2C(0, scl=Pin(18), sda=Pin(19), freq=100000)
    adresses = i2c.scan()                # on cherche l'adresse de l'ecran
    ecran = EcranLCD(i2c, adresses[0])
except Exception:
    ecran = None                         # pas d'ecran : le programme continue sans
    print("Ecran LCD non detecte")

def sans_accents(texte):
    # l'ecran LCD ne connait pas les accents : on les remplace
    accents = {"é": "e", "è": "e", "ê": "e", "ë": "e", "à": "a", "â": "a", "ù": "u",
               "û": "u", "ô": "o", "î": "i", "ï": "i", "ç": "c", "É": "E", "È": "E",
               "Ê": "E", "À": "A", "Â": "A", "Ç": "C", "Ô": "O", "Î": "I", "Ù": "U"}
    resultat = ""
    for c in texte:
        if c in accents:
            resultat = resultat + accents[c]
        elif ord(c) > 127:
            resultat = resultat + "?"
        else:
            resultat = resultat + c
    return resultat

def afficher(ligne1, ligne2):
    if ecran is None:
        return
    try:
        ecran.ecrire_ligne(0, sans_accents(ligne1))
        ecran.ecrire_ligne(1, sans_accents(ligne2))
    except Exception:
        pass

# ================= Emission =================
def envoyer_trame(texte):
    bits = bits_from_bytes(utf8_bytes(texte))      # texte -> UTF-8 -> bits
    mbits = manchester_encode("0" + bits)          # bit de synchro "0" + Manchester
    DE.value(1)                                    # on prend la ligne
    DI.value(1)
    time.sleep_ms(6 * DEMI_BIT)
    debut = time.ticks_us()
    for k in range(len(mbits)):                    # un demi-bit toutes les DEMI_BIT ms
        DI.value(int(mbits[k]))
        instant = time.ticks_add(debut, (k + 1) * DEMI_BIT_US)
        while time.ticks_diff(instant, time.ticks_us()) > 0:
            pass
    DI.value(1)
    time.sleep_ms(4 * DEMI_BIT)
    DE.value(0)                                    # on relache la ligne

# ================= Reception =================
SPS = 10                      # nombre de lectures par demi-bit (comme sps en cours)
PERIODE = DEMI_BIT_US // SPS  # temps entre deux lectures

def lire_signal(debut):
    # lit la ligne SPS fois par demi-bit, a partir de l'instant "debut"
    signal = []
    repos = 0
    k = 0
    while repos < 4 * SPS:                  # 2 bits entiers au repos = fin de trame
        instant = time.ticks_add(debut, k * PERIODE + PERIODE // 2)
        while time.ticks_diff(instant, time.ticks_us()) > 0:
            pass                            # on attend le moment de la lecture
        v = RO.value()
        signal.append(v)
        if v == 1:
            repos = repos + 1
        else:
            repos = 0
        k = k + 1
    return signal

def demi_bits_depuis_signal(signal):
    # meme principe que decode_nrz : moyenne par paquet de SPS lectures
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
    # on garde les paires valides ; la premiere paire "11" = retour au repos
    mbits = ""
    for i in range(0, len(m) - 1, 2):
        if m[i:i+2] == "10" or m[i:i+2] == "01":
            mbits = mbits + m[i:i+2]
        else:
            break
    bits = manchester_decode(mbits)                # Manchester -> bits (cours)
    if len(bits) < 9 or bits[0] != "0":
        raise ValueError("Bit de synchro absent")
    return bytes_from_bits(bits[1:]).decode('utf-8')   # bits -> octets -> texte UTF-8

def ecouter_bus(duree_ms):
    # renvoie l'instant ou une trame commence, ou None si la ligne reste au repos
    fin = time.ticks_add(time.ticks_ms(), duree_ms)
    while time.ticks_diff(fin, time.ticks_ms()) > 0:
        if RO.value() == 0:
            return time.ticks_us()
    return None

# ================= Datagramme =================
def construire_trame():
    try:
        capteur.measure()
        t = capteur.temperature()
        msg = MESSAGE
        if t > 30 and MESSAGE == "OK":
            msg = "ALERTE"                         # alerte automatique si trop chaud
    except Exception:
        t = "ERR"
        msg = "CAPTEUR"
    return "<" + STATION + ":T=" + str(t) + ";V=" + str(VIVRES) + ";MSG=" + msg + ">"

def analyser_trame(texte):
    corps = texte[1:-1]                            # on enleve < et >
    station, champs = corps.split(":", 1)
    donnees = {}
    for champ in champs.split(";"):
        if "=" in champ:
            cle, valeur = champ.split("=", 1)
            donnees[cle] = valeur
    return station, donnees

def traiter(signal):
    try:
        texte = decoder_trame(signal)
    except Exception:
        print("Trame invalide")
        afficher("Reception :", "Trame invalide")
        return
    if not (texte.startswith("<") and texte.endswith(">") and ":" in texte):
        print("Trame incomplete :", texte)
        afficher("Reception :", "Trame incomplete")
        return
    station, d = analyser_trame(texte)
    afficher("De " + station + " T:" + d.get("T", "?") + "C",
             "V:" + d.get("V", "?") + "% " + d.get("MSG", "?"))
    print("Recu de", station, ":", texte)
    print("   Temperature :", d.get("T", "?"), "C")
    print("   Vivres      :", d.get("V", "?"), "%")
    print("   Etat        :", d.get("MSG", "?"))

# ================= Saisie au clavier (console Thonny) =================
clavier = select.poll()
clavier.register(sys.stdin, select.POLLIN)
flux = getattr(sys.stdin, "buffer", sys.stdin)   # lecture en octets (UTF-8)
saisie = b""

def lire_clavier():
    # renvoie une ligne tapee dans la console, ou None (sans bloquer le programme)
    global saisie
    while clavier.poll(0):
        c = flux.read(1)
        if isinstance(c, str):
            c = c.encode('utf-8')
        if c == b"\n" or c == b"\r":
            if saisie != b"":
                ligne = saisie.decode('utf-8')
                saisie = b""
                return ligne
        else:
            saisie = saisie + c
    return None

AIDE = """Commandes (tapez puis Entree) :
  V=75            -> vivres a 75 %
  ALERTE          -> message ALERTE
  V=75 ALERTE     -> vivres ET message en une fois
  AIDE            -> afficher cette aide"""

def traiter_commande(ligne):
    # renvoie True si une nouvelle trame doit etre envoyee
    global VIVRES, MESSAGE
    ligne = ligne.strip().upper()
    if ligne == "AIDE":
        print(AIDE)
        return False
    if not EMETTEUR:
        print("Station en reception seule : elle n'envoie pas de trame")
        return False
    nouveau_vivres = VIVRES
    mots_message = []
    for mot in ligne.split(" "):
        if mot == "":
            continue
        if mot.startswith("V="):                   # partie vivres
            try:
                nouveau_vivres = int(mot[2:])
            except ValueError:
                print("Vivres invalides : tapez par exemple V=75")
                return False
            if nouveau_vivres < 0 or nouveau_vivres > 100:
                print("Les vivres doivent etre entre 0 et 100")
                return False
        else:                                      # partie message
            mots_message.append(mot)
    nouveau_message = " ".join(mots_message)
    if nouveau_message != "":
        for c in nouveau_message:
            if c in "<>:;=":                       # ces caracteres decoupent la trame
                print("Caractere interdit dans le message :", c)
                return False
        if len(nouveau_message) > 12:
            print("Le message doit faire 12 caracteres maximum")
            return False
        MESSAGE = nouveau_message
    VIVRES = nouveau_vivres
    print("-> Vivres =", VIVRES, "% | Message =", MESSAGE)
    afficher("V:" + str(VIVRES) + "% modifie", MESSAGE)
    return True

# ================= Boucle principale =================
print("Station", STATION, "prete")
if EMETTEUR:
    # ----- questions au demarrage -----
    afficher("Abri " + STATION, "Saisir vivres")
    while True:
        reponse = input("Vivres restants (0 a 100 %) : ").strip()
        try:
            v = int(reponse)
        except ValueError:
            print("Tapez un nombre entier, par exemple 80")
            continue
        if 0 <= v <= 100:
            VIVRES = v
            break
        print("Les vivres doivent etre entre 0 et 100")
    afficher("Abri " + STATION, "Saisir message")
    while True:
        reponse = input("Message a envoyer (ex: OK, ALERTE) : ").strip().upper()
        if reponse == "":
            print("Le message ne peut pas etre vide")
            continue
        interdit = False
        for c in reponse:
            if c in "<>:;=":
                interdit = True
        if interdit:
            print("Caracteres interdits : < > : ; =")
            continue
        if len(reponse) > 12:
            print("Le message doit faire 12 caracteres maximum")
            continue
        MESSAGE = reponse
        break
    print("-> Vivres =", VIVRES, "% | Message =", MESSAGE)
    print(AIDE)
else:
    print("Mode reception seule : la station affiche les trames recues")
afficher("Abri " + STATION, "En attente...")
prochain = time.ticks_add(time.ticks_ms(), random.randint(2000, 6000))
a_envoyer = None
if EMETTEUR:
    a_envoyer = construire_trame()                 # premiere trame envoyee tout de suite

while True:
    ligne = lire_clavier()                         # l'utilisateur a-t-il tape quelque chose ?
    if ligne is not None:
        if traiter_commande(ligne):
            a_envoyer = construire_trame()         # on envoie tout de suite la nouvelle trame
    debut = ecouter_bus(5 * 2 * DEMI_BIT)          # on ecoute pendant 5 bits
    if debut is not None:                          # bus occupe : quelqu'un parle
        if a_envoyer:
            print("Bus occupe -> envoi reporte")
            afficher("Bus occupe", "Envoi reporte")
        traiter(lire_signal(debut))
        continue
    if a_envoyer:                                  # bus libre : on peut parler
        print("Bus libre -> envoi :", a_envoyer)
        envoyer_trame(a_envoyer)
        station, d = analyser_trame(a_envoyer)
        afficher("Envoi " + STATION + " T:" + d["T"] + "C",
                 "V:" + d["V"] + "% " + d["MSG"])
        a_envoyer = None
        prochain = time.ticks_add(time.ticks_ms(), PERIODE_MS + random.randint(0, 3000))
    elif EMETTEUR and time.ticks_diff(time.ticks_ms(), prochain) >= 0:
        a_envoyer = construire_trame()             # on prepare, envoi au prochain silence
