import json
import numpy as np

O = json.load(open("site/_wrproj.json"))
P = json.load(open("wrparams.json"))
FCT = (11.18 - 5.151) / 8.094

r = sorted([v for v in O.values() if v["pos"] == "WR"],
           key=lambda x: -x["ppg"])
print("=== WR RANKINGS 1-50 (20,000 sims per game) ===")
print("  %-3s %-24s %-4s %7s %7s %7s %7s"
      % ("#", "PLAYER", "TM", "PPG", "FLOOR", "CEIL", "TGT%"))
for i, v in enumerate(r[:50], 1):
    w = [x for x in v["wk"] if x["o"] != "BYE"
         and not x.get("out")]
    if not w:
        continue
    k = [kk for kk, p in P.items() if p["n"] == v["n"]]
    ts = P[k[0]]["tshare"] * 100 if k else 0
    print("  %-3d %-24s %-4s %7.1f %7.1f %7.1f %6.1f%%"
          % (i, v["n"][:24], v["tm"], v["ppg"],
             np.mean([x["lo"] for x in w]),
             np.mean([x["hi"] for x in w]), ts))

print("\n=== TE RANKINGS 1-20 ===")
t = sorted([v for v in O.values() if v["pos"] == "TE"],
           key=lambda x: -x["ppg"])[:20]
for i, v in enumerate(t, 1):
    print("  %-3d %-24s %-4s %7.1f"
          % (i, v["n"][:24], v["tm"], v["ppg"]))

def decomp(name):
    k = [kk for kk, p in P.items() if p["n"] == name]
    if not k:
        return None
    p = P[k[0]]
    tg = p["tmatt"] * p["tshare"]
    cr = min(.90, max(.35, p["crate"]
                      * (1 - .012 * (p["adot"] - 8.094))))
    rec = tg * cr
    ypr = p["adot"] * FCT + p["yac"]
    return {"n": name, "tmatt": p["tmatt"],
            "ts": p["tshare"], "tg": tg, "cr": cr,
            "rec": rec, "adot": p["adot"], "yac": p["yac"],
            "ypr": ypr, "yds": rec * ypr,
            "td": tg * p["tdt"],
            "pts": rec + rec * ypr * .1 + tg * p["tdt"] * 6}

print("\n=== WHY OLAVE IS AHEAD OF CHASE ===")
A, B = decomp("Chris Olave"), decomp("Ja'Marr Chase")
rows = [("team targets/gm", "tmatt", "%6.1f"),
        ("his target share", "ts", "%5.1f%%"),
        ("-> targets/gm", "tg", "%6.1f"),
        ("catch rate", "cr", "%5.1f%%"),
        ("-> catches/gm", "rec", "%6.1f"),
        ("aDOT (air yds/tgt)", "adot", "%6.1f"),
        ("YAC per catch", "yac", "%6.1f"),
        ("-> yds per catch", "ypr", "%6.1f"),
        ("-> yards/gm", "yds", "%6.1f"),
        ("-> TD/gm", "td", "%6.2f"),
        ("BASE PPR pts", "pts", "%6.1f")]
print("  %-22s %10s %10s %9s"
      % ("", "OLAVE", "CHASE", "EDGE"))
for lbl, kk, f in rows:
    a, b = A[kk], B[kk]
    if "%%" in f:
        sa, sb = f % (a * 100), f % (b * 100)
    else:
        sa, sb = f % a, f % b
    print("  %-22s %10s %10s %+8.1f%%"
          % (lbl, sa, sb, (a / b - 1) * 100 if b else 0))

print("\n=== PER-WEEK VARIATION (opponent + venue) ===")
for nm in ("Chris Olave", "Ja'Marr Chase",
           "Jaxon Smith-Njigba"):
    v = [x for x in O.values() if x["n"] == nm]
    if not v:
        continue
    w = [x for x in v[0]["wk"] if x["o"] != "BYE"][:8]
    print("  %-20s %s" % (nm[:20], "  ".join(
        "%s%s %.1f" % (x["o"], "H" if x.get("h") else "A",
                       x["m"]) for x in w)))
    m = [x["m"] for x in v[0]["wk"] if x["o"] != "BYE"]
    print("  %-20s range %.1f to %.1f  (spread %.1f pts)"
          % ("", min(m), max(m), max(m) - min(m)))
