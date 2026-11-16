import json
import numpy as np
import nflreadpy as nfl

QB = json.load(open("qbparams.json"))
P = json.load(open("site/_qbproj.json"))
TT = json.load(open("teamtotal.json"))

rk = sorted([v for v in P.values() if v.get("qb1")],
            key=lambda x: -x["ppg"])[:14]
print("%-3s %-19s %-4s %6s | %5s %5s %6s %6s | %5s %5s"
      % ("#", "QB", "TM", "PPG", "ATT", "YPA", "PASSY",
         "PASTD", "CAR", "RUSH"))
print("-" * 84)
for i, v in enumerate(rk, 1):
    k = [kk for kk, x in QB.items() if x["n"] == v["n"]]
    if not k:
        continue
    p = QB[k[0]]
    py = p["att"] * p["ypa"]
    ptd = p["att"] * p["ptd"]
    ry = p["car"] * p["ypc"]
    rtd = p["car"] * p["rtd"]
    print("%-3d %-19s %-4s %6.1f | %5.1f %5.2f %6.0f %6.2f |"
          " %5.1f %5.1f"
          % (i, v["n"][:19], v["tm"], v["ppg"], p["att"],
             p["ypa"], py, ptd, p["car"], ry * .1 + rtd * 6))

print("\n=== SAMPLE SIZE: how much is each QB trusted? ===")
print("%-20s %6s %7s %8s %8s"
      % ("QB", "GAMES", "N_EFF", "ATT", "IMPLIED"))
for v in rk:
    k = [kk for kk, x in QB.items() if x["n"] == v["n"]]
    if not k:
        continue
    p = QB[k[0]]
    it = TT["avg"].get(p["tm"], TT["lg"])
    print("%-20s %6d %7.2f %8.1f %8.2f%s"
          % (p["n"][:20], p["g"], p["neff"], p["att"], it,
             "   <-- thin sample" if p["neff"] < 3.5 else ""))

print("\n=== league attempt leaders (the volume story) ===")
a = sorted([x for x in QB.values() if x["qb1"]],
           key=lambda x: -x["att"])[:8]
for p in a:
    it = TT["avg"].get(p["tm"], TT["lg"])
    print("   %-20s %5.1f att   implied %5.2f   %s"
          % (p["n"][:20], p["att"], it,
             "LOW-SCORING OFFENSE" if it < 21 else ""))
