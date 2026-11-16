import json, re, datetime
import numpy as np
import nflreadpy as nfl

SIMS = 20000
np.random.seed(13)
_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

P = json.load(open("wrparams.json"))
HFA = json.load(open("hfa.json"))
TT = json.load(open("teamtotal.json"))
DR = json.load(open("site/_defrank.json"))
LGT, SLOPE = TT["lg"], TT["slope"]
DEF = DR.get("def", DR)
LGA, LGY = 8.094, 5.151
try:
    QNOW = json.load(open("qbindex.json"))["now"]
except Exception:
    QNOW = {}
try:
    SM = json.load(open("sharemult.json"))
except Exception:
    SM = {}
FCT = (11.18 - LGY) / LGA          # depth->yards factor

def dm(team, key):
    v = DEF.get(team)
    if isinstance(v, dict):
        for k in (key, "m_ypa", "m_cr"):
            if k in v:
                try:
                    x = float(v[k])
                    if 0.5 < x < 1.8:
                        return x
                except Exception:
                    pass
    return 1.0

def om(team, wk):
    t = TT["wk"].get(team, {}).get(str(wk))
    if t is None:
        t = TT["avg"].get(team, LGT)
    return min(1.28, max(0.75,
                         1.0 + SLOPE * (t - LGT) / 17.5))

sc = nfl.load_schedules([2026]).to_pandas()
SCH = {}
for _, g in sc.iterrows():
    w = int(g["week"])
    SCH.setdefault(g["home_team"], {})[w] = (g["away_team"], 1)
    SCH.setdefault(g["away_team"], {})[w] = (g["home_team"], 0)

def sim(p, opp, home, wk, key=None):
    n = SIMS
    # teammates returning from injury take targets back
    sm = SM.get(key, {}).get(str(wk), 1.0) if key else 1.0
    o = om(p["tm"], wk)
    d = dm(opp, "m_ypa")
    h = HFA.get(p["pos"], HFA.get("WR", 1.02))
    hm = h if home else 1.0 / h

    # team pass volume, then his share of it
    tv = p["tmatt"] * (o ** 0.45)
    tg = np.random.normal(tv * p["tshare"] * sm,
                          max(1.4, p["sd_t"] * 0.8), n)
    tg = np.clip(tg, 0, 22)

    # deeper targets are caught less often (corr -0.35)
    cr = p["crate"] * (1 - 0.012 * (p["adot"] - LGA))
    cr = min(0.90, max(0.35, cr))
    rec = np.random.binomial(np.round(tg).astype(int), cr)

    # re-apply the quality of whoever is throwing NOW
    qn = QNOW.get(p["tm"], 1.0)
    ypr = np.random.normal(
        (p["adot"] * FCT + p["yac"]) * d * (hm ** .5) * qn,
        4.2, n)
    ypr = np.clip(ypr, 1.0, 34.0)
    yds = rec * ypr

    td = np.random.poisson(
        np.clip(tg * p["tdt"] * o * d * qn, 0, 4))
    return rec * 1.0 + yds * 0.1 + td * 6.0

OUT = {}
for k, p in P.items():
    if p["tm"] not in SCH:
        continue
    wks = []
    for w in range(CUR, 18):
        m = SCH[p["tm"]].get(w)
        if not m:
            wks.append({"w": w, "o": "BYE", "m": 0.0})
            continue
        s = sim(p, m[0], m[1], w, k)
        _out = SM.get(k, {}).get(str(w), 1.0) == 0.0
        wks.append({"w": w, "o": m[0], "h": m[1],
                    "out": 1 if _out else 0,
                    "m": round(float(s.mean()), 2),
                    "sd": round(float(s.std()), 2),
                    "lo": round(float(np.percentile(s, 10)), 1),
                    "hi": round(float(np.percentile(s, 90)), 1)})
    # ppg is his RATE WHEN PLAYING. Games missed are
    # handled by games-remaining, not by averaging in
    # zeros -- otherwise injury is counted twice.
    pl = [x["m"] for x in wks
          if x["o"] != "BYE" and not x.get("out")]
    if not pl:
        pl = [0.0]
    OUT[k] = {"n": p["n"], "pos": p["pos"], "tm": p["tm"],
              "ppg": round(float(np.mean(pl)), 2), "wk": wks}
json.dump(OUT, open("site/_wrproj.json", "w"),
          separators=(",", ":"))
print("simulated %d pass-catchers x %d wks x %d sims"
      % (len(OUT), 18 - CUR, SIMS))

for pos in ("WR", "TE"):
    r = sorted([v for v in OUT.values() if v["pos"] == pos],
               key=lambda x: -x["ppg"])[:14]
    print("\n=== %s RANKINGS (20k sims) ===" % pos)
    print("  %-3s %-24s %-4s %7s %7s %7s"
          % ("#", "PLAYER", "TM", "PPG", "FLOOR", "CEIL"))
    for i, v in enumerate(r, 1):
        w = [x for x in v["wk"] if x["o"] != "BYE"]
        print("  %-3d %-24s %-4s %7.1f %7.1f %7.1f"
              % (i, v["n"][:24], v["tm"], v["ppg"],
                 np.mean([x["lo"] for x in w]),
                 np.mean([x["hi"] for x in w])))
