import json, re, datetime
import numpy as np

_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

P = json.load(open("wrparams.json"))
try:
    INJ = json.load(open("site/_injtime.json"))
except Exception:
    INJ = {}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

# what fraction of a team's targets our modelled players
# should account for (rest go to depth/FB/unmodelled)
CAP = 0.94

TEAMS = {}
for k, p in P.items():
    TEAMS.setdefault(p["tm"], []).append(k)

# A team has ~6 real pass-catchers. Measured: the top 6
# already sum to 96.4%, almost exactly the 94% target.
# It is the TAIL -- 3-game backups carrying inflated
# per-game shares -- that pushes teams to 130%+.
# Normalize the core gently; compress the tail hard.
CORE_N = 6
TAIL_BUDGET = 0.06

print("=== TEAMS OVER-ALLOCATED (shares summed > %.0f%%) ==="
      % (CAP * 100))
print("%-5s %9s %9s  %s" % ("TEAM", "SUM", "SCALED", "TOP 3"))
BASE = {}
for tm, ks in sorted(TEAMS.items()):
    ks = sorted(ks, key=lambda k: -P[k]["tshare"])
    core, tail = ks[:CORE_N], ks[CORE_N:]
    ctot = sum(P[k]["tshare"] for k in core)
    ttot = sum(P[k]["tshare"] for k in tail)
    csc = (CAP / ctot) if ctot > 0 else 1.0
    tsc = (TAIL_BUDGET / ttot) if ttot > 0 else 1.0
    for k in core:
        BASE[k] = P[k]["tshare"] * csc
    for k in tail:
        BASE[k] = P[k]["tshare"] * tsc
    tot = ctot + ttot
    if tot > CAP * 1.15:
        top = core[:3]
        print("%-5s %8.1f%% %8.1f%%  %s"
              % (tm, tot * 100, CAP * 100,
                 ", ".join("%s %.0f%%->%.0f%%"
                           % (P[k]["n"].split()[-1],
                              P[k]["tshare"] * 100,
                              BASE[k] * 100) for k in top)))

# weeks each player misses
MISS = {}
for k, p in P.items():
    v = INJ.get(norm(p["n"]))
    if not v:
        continue
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
            # vacated targets redistribute by existing share
            add = free * (BASE[k] / live) if live > 0 else 0
            OUT.setdefault(k, {})[str(w)] = round(
                (BASE[k] + add) / max(1e-9, P[k]["tshare"]), 4)
        for k in gone:
            OUT.setdefault(k, {})[str(w)] = 0.0
json.dump(OUT, open("sharemult.json", "w"),
          separators=(",", ":"))
print("\nwrote sharemult.json (%d players)" % len(OUT))

print("\n=== LA RAMS: the Puka effect ===")
la = [k for k in TEAMS.get("LA", [])
      if P[k]["tshare"] > 0.08]
la.sort(key=lambda k: -P[k]["tshare"])
hdr = "  %-22s %7s" % ("PLAYER", "RAW")
for w in range(CUR, CUR + 5):
    hdr += " %6s" % ("wk" + str(w))
print(hdr)
for k in la:
    row = "  %-22s %6.1f%%" % (P[k]["n"][:22],
                               P[k]["tshare"] * 100)
    for w in range(CUR, CUR + 5):
        m = OUT.get(k, {}).get(str(w), 1.0)
        row += " %5.1f%%" % (P[k]["tshare"] * m * 100)
    print(row)
for k in la:
    if k in MISS:
        print("  (%s out %s wk)"
              % (P[k]["n"], MISS[k] if MISS[k] < 99 else "SEASON"))
