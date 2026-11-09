import numpy as np
import matplotlib.pyplot as plt

def manchester_encode(bits: str) -> str:
    # '1' -> '10' (haut puis bas), '0' -> '01' (bas puis haut)
    resultat = ""
    for b in bits:
        if b == "1":
            resultat += "10"
        else:
            resultat += "01"
    return resultat

def manchester_decode(mbits: str) -> str:
    # lit les demi-bits deux par deux : '10' -> '1', '01' -> '0', erreur sinon
    resultat = ""
    for i in range(0, len(mbits), 2):
        paire = mbits[i:i + 2]
        if paire == "10":
            resultat += "1"
        elif paire == "01":
            resultat += "0"
        else:
            raise ValueError("Pas de transition au milieu du bit : " + paire)
    return resultat

bits = "10110"
m = manchester_encode(bits)
dec = manchester_decode(m)
assert dec == bits, f"Décodage différent (dec={dec})"
print("Bits :", bits, "-> Manchester :", m)

wf = np.repeat([int(c) for c in m], 32)        # chaque demi-bit répété 32 fois pour le tracé
plt.figure(figsize=(8, 2.2))
plt.plot(np.arange(wf.size) / 64, wf)
plt.title("Manchester — '1'→10, '0'→01 (niveau haut/bas par demi-bit)")
plt.xlabel("Bits (échelle)"); plt.ylabel("Niveau")
plt.grid(True); plt.tight_layout(); plt.show()
print("✅ Test Manchester OK")
