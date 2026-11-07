import numpy as np
import matplotlib.pyplot as plt
def encode_nrz(bits: str, sps: int = 100, high: float = 1.0, low: float = -1.0) -> np.ndarray:
    encode = []
    for c in bits:
        if c == "0":
            l = []
            for i in range(sps):
                l.append(low)
            encode = encode+l
        elif c == "1":
            l=[]
            for i in range(sps):
                l.append(high)
            encode = encode+l
        else:
            print("Erreur ce n'est ni un 0 ni un 0")
    return np.array(encode)

def decode_nrz(sig: np.ndarray, sps: int = 100, high: float = 1.0, low: float = -1.0) -> str:
    m=""
    for s in range(0,len(sig),sps):
        moy = sum(sig[s:s+sps])/sps
        if moy >= 0:
            m=m+"1"
        else :
            m=m+"0"
    return m
# Tests NRZ
bits = "10110010"
sps = 64
try:
    x = encode_nrz(bits, sps=sps, high=1.0, low=-1.0)
    pred = decode_nrz(x, sps=sps, high=1.0, low=-1.0)
    assert pred == bits, f"Décodage différent (pred={pred})"
    # Visualisation (zoom 10 bits max)
    plt.figure(figsize=(8,2.2))
    t = np.arange(x.size)/sps
    plt.plot(t, x)
    plt.title("NRZ-L — entrée/sortie cohérentes")
    plt.xlabel("Bits (échelle)"); plt.ylabel("Niveau")
    plt.grid(True); plt.tight_layout(); plt.show()
    print("✅ Test NRZ OK")
except NotImplementedError:
    print("⚠️ Implémente d'abord encode_nrz/decode_nrz")
