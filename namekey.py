"""Canonical player-name key. Use this everywhere.

Sleeper says "Kenneth Walker", our board says
"Kenneth Walker III". Same player. Suffixes must be
stripped on BOTH sides or rosters silently lose players.
Team defenses need their own handling: "Browns" vs
"Browns Defense" vs "CLE".
"""
import re

SUF = {"jr", "sr", "ii", "iii", "iv", "v"}

TEAMFIX = {"LAR": "LA", "OAK": "LV", "SD": "LAC",
           "STL": "LA", "ARZ": "ARI", "BLT": "BAL",
           "CLV": "CLE", "HST": "HOU", "WSH": "WAS",
           "JAC": "JAX"}

def nk(s):
    """name key: lowercase, letters only, suffix stripped"""
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    p = re.sub(r"\s+", " ", s).strip().split()
    while p and p[-1] in SUF:
        p.pop()
    return " ".join(p)

def tfix(t):
    t = (t or "").upper()
    return TEAMFIX.get(t, t)

def dk(s):
    """defense key: 'Browns Defense' / 'Browns' -> 'browns'"""
    k = nk(s)
    for w in (" defense", " dst", " d st", " def"):
        if k.endswith(w):
            k = k[:-len(w)]
    return k.strip()

def index(rows, name_of=lambda r: r.get("n"),
          pos_of=lambda r: r.get("pos")):
    """build a lookup that resolves both players and DSTs"""
    ix = {}
    for r in rows:
        n = name_of(r)
        if not n:
            continue
        if (pos_of(r) or "") in ("DEF", "DST"):
            ix.setdefault(dk(n), r)
        ix.setdefault(nk(n), r)
    return ix

def find(ix, name, pos=None):
    if (pos or "") in ("DEF", "DST"):
        r = ix.get(dk(name))
        if r:
            return r
    return ix.get(nk(name))
