import json, re, datetime
import numpy as np

_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

P = json.load(open("rbparams.json"))
try:
    INJ = json.load(open("site/_injtime.json"))
except Exception:
    INJ = {}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

# RBs take ~83% of team carries (measured 2026).
# Shrunk shares already sum to ~103%, so the old 82% cap
# was cutting every workhorse by a fifth. The real problem
# is STALE backups: Vidal carries 37% from games when
# Hampton was not on the team. Anchor on the backfield
# that exists NOW.
CAP = 0.83
W26 = 0.65      # weight on actual 2026 distribution

import nflreadpy as _nfl
_d = _nfl.load_player_stats([2026]).to_pandas()
_d["carries"] = _d["carries"].fillna(0).astype(float)
_d = _d[_d["carries"] > 0]
_tc = _d.groupby("team")["carries"].sum().to_dict()
_pa = _d.groupby(["player_display_name", "team"],
                 as_index=False)["carries"].sum()
CUR26 = {}
for _, _r in _pa.iterrows():
    t = _tc.get(_r["team"], 0)
    if t > 0:
        CUR26[norm(_r["player_display_name"])] = \
            _r["carries"] / t
print("2026 carry shares for %d players" % len(CUR26))

TEAMS = {}
for k, p in P.items():
    TEAMS.setdefault(p["tm"], []).append(k)

BASE = {}
print("=== BACKFIELD SHARES (normalized) ===")
for tm, ks in sorted(TEAMS.items()):
    ks = sorted(ks, key=lambda k: -P[k]["cshare"])
    blend = {}
    for k in ks:
        a26 = CUR26.get(k)
        blend[k] = (W26 * a26 + (1 - W26) * P[k]["cshare"]
                    if a26 is not None else
                    P[k]["cshare"] * 0.45)
    tot = sum(blend.values())
    sc = (CAP / tot) if tot > CAP else 1.0
    for k in ks:
        BASE[k] = blend[k] * sc
    core = ks[:3]
    if tm in ("NO", "DEN", "LAC", "PIT", "TB", "PHI"):
        print("  %-4s %s" % (tm, ",  ".join(
            "%s %.0f%%->%.0f%%" % (P[k]["n"].split()[-1][:10],
                                   P[k]["cshare"] * 100,
                                   BASE[k] * 100)
            for k in core)))

MISS = {}
for k, p in P.items():
    v = INJ.get(norm(p["n"]))
    if v:
        MISS[k] = 99 if v["weeks"] >= 99 else v["weeks"]

OUT = {}
for tm, ks in TEAMS.items():
    for w in range(CUR, 18):
        act, gone = [], []
        for k in ks:
            m = MISS.get(k, 0)
            if m >= 99 or (m > 0 and w < CUR + m):
                gone.append(k)
            else:
                act.append(k)
        free = sum(BASE[k] for k in gone)
        live = sum(BASE[k] for k in act)
        for k in act:
            add = free * (BASE[k] / live) if live > 0 else 0
            OUT.setdefault(k, {})[str(w)] = round(
                (BASE[k] + add) / max(1e-9, P[k]["cshare"]), 4)
        for k in gone:
            OUT.setdefault(k, {})[str(w)] = 0.0
json.dump(OUT, open("rbsharemult.json", "w"),
          separators=(",", ":"))
print("\nwrote rbsharemult.json (%d RBs)" % len(OUT))

print("\n=== INJURED RBs ===")
for k, m in sorted(MISS.items(), key=lambda x: -x[1]):
    print("  %-24s %-4s  out %s"
          % (P[k]["n"][:24], P[k]["tm"],
             "SEASON" if m >= 99 else "%d wk" % m))

print("\n=== NEW ORLEANS backfield week by week ===")
no = sorted(TEAMS.get("NO", []), key=lambda k: -BASE[k])
hdr = "  %-22s %7s" % ("PLAYER", "BASE")
for w in range(CUR, CUR + 5):
    hdr += " %6s" % ("wk" + str(w))
print(hdr)
for k in no[:4]:
    row = "  %-22s %6.1f%%" % (P[k]["n"][:22], BASE[k] * 100)
    for w in range(CUR, CUR + 5):
        m = OUT.get(k, {}).get(str(w), 1.0)
        row += " %5.1f%%" % (P[k]["cshare"] * m * 100)
    print(row)
