import json
import pandas as pd

B = pd.read_csv("board_final.csv")
D = B[B["position"] == "DST"].copy()
print("canonical defenses on board: %d" % len(D))

FIX = {"LA": "lar", "WAS": "wsh"}
LOGO = "https://a.espncdn.com/i/teamlogos/nfl/500/%s.png"
SCH = json.load(open("site/_sched.json"))["sched"]

def bye(t):
    wk = set(int(w) for w in SCH.get(t, {}))
    for i in range(4, 15):
        if i not in wk:
            return i
    return None

CANON = {}
for _, r in D.iterrows():
    t = str(r["team"])
    CANON[t] = {
        "nm": str(r["player_display_name"]),
        "tm": t, "ppg": round(float(r["points"]), 2),
        "by": bye(t),
        "logo": LOGO % FIX.get(t, t.lower()),
        "p10": float(r.get("p10") or 0),
        "p50": float(r.get("p50") or 0),
        "p90": float(r.get("p90") or 0)}
print("canonical map built: %d teams" % len(CANON))

def isdef(x):
    return str(x.get("ps") or x.get("p") or "").upper() \
        in ("DST", "DEF", "D/ST")

P = json.load(open("site/_proj.json"))
before = len([1 for v in P.values() if isdef(v)])
P = {k: v for k, v in P.items() if not isdef(v)}
for t, c in CANON.items():
    P[t] = {"nm": c["nm"], "ps": "DST", "tm": t,
            "ppg": c["ppg"], "by": c["by"], "rk": 900,
            "prk": 0, "st": "", "logo": c["logo"]}
order = sorted(CANON, key=lambda x: -CANON[x]["ppg"])
for i, t in enumerate(order):
    P[t]["prk"] = i + 1
json.dump(P, open("site/_proj.json", "w"))
print("_proj.json defenses: %d -> %d (keyed by team)"
      % (before, len(CANON)))

R = json.load(open("site/_dr.json"))
before = len([1 for x in R if isdef(x)])
R = [x for x in R if not isdef(x)]
for i, t in enumerate(order):
    c = CANON[t]
    R.append({"i": t, "n": c["nm"], "p": "DST", "t": t,
              "by": c["by"], "hs": c["logo"],
              "rk": 900 + i, "prk": i + 1, "adp": None,
              "pts": round(c["ppg"] * 17, 1),
              "avg": c["ppg"], "car": 0, "ryd": 0,
              "rtd": 0, "tar": 0, "rec": 0, "cyd": 0,
              "ctd": 0, "patt": 0, "pyd": 0, "ptd": 0,
              "gm": 17, "st": "", "edge": None})
json.dump(R, open("site/_dr.json", "w"))
print("_dr.json defenses: %d -> %d (with logos)"
      % (before, len(CANON)))

T = json.load(open("site/_tc.json"))
n = 0
for x in T:
    if isdef(x):
        c = CANON.get(str(x.get("t")))
        if c:
            x["logo"] = c["logo"]
            x["g"] = c["ppg"]
            n += 1
json.dump(T, open("site/_tc.json", "w"))
print("_tc.json defenses given logos: %d" % n)

Q = json.load(open("site/_qr.json"))
if "DST" not in Q or len(Q.get("DST", [])) < 50:
    try:
        q = pd.read_csv("dst_quant.csv")
        lo, mid, hi = (float(q["q10"][0]), float(q["q50"][0]),
                       float(q["q90"][0]))
        Q["DST"] = [round(lo + (hi - lo) * (i / 98.0), 3)
                    for i in range(99)]
        json.dump(Q, open("site/_qr.json", "w"))
        print("_qr.json: DST distribution added")
    except Exception as e:
        print("_qr DST skipped: %s" % e)

print("\n=== TOP 8 DEFENSES (canonical) ===")
for t in order[:8]:
    c = CANON[t]
    print("  %-4s %-22s %5.2f ppg  bye %s"
          % (t, c["nm"], c["ppg"], c["by"]))
