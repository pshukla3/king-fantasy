import json, re, datetime
import numpy as np
import nflreadpy as nfl

SIMS = 20000
np.random.seed(17)
_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

R = json.load(open("rbparams.json"))
W = json.load(open("wrparams.json"))
HFA = json.load(open("hfa.json"))
TT = json.load(open("teamtotal.json"))
TP = json.load(open("tushpush.json"))
DR = json.load(open("site/_defrank.json"))
DEF = DR.get("def", DR)
LGT, SLOPE = TT["lg"], TT["slope"]
QSH = TP["qb_share"]
LGQ = float(np.mean(list(QSH.values())))
LGA, LGY = 8.094, 5.151
FCT = (11.18 - LGY) / LGA
try:
    SM = json.load(open("sharemult.json"))
except Exception:
    SM = {}
try:
    RSM = json.load(open("rbsharemult.json"))
except Exception:
    RSM = {}
try:
    QNOW = json.load(open("qbindex.json"))["now"]
except Exception:
    QNOW = {}

def dm(team, key):
    v = DEF.get(team)
    if isinstance(v, dict) and key in v:
        try:
            x = float(v[key])
            if 0.5 < x < 1.8:
                return x
        except Exception:
            pass
    return 1.0

def om(team, wk):
    t = TT["wk"].get(team, {}).get(str(wk))
    if t is None:
        t = TT["avg"].get(team, LGT)
    return min(1.28, max(0.75, 1 + SLOPE * (t - LGT) / 17.5))

sc = nfl.load_schedules([2026]).to_pandas()
SCH = {}
for _, g in sc.iterrows():
    w = int(g["week"])
    SCH.setdefault(g["home_team"], {})[w] = (g["away_team"], 1)
    SCH.setdefault(g["away_team"], {})[w] = (g["home_team"], 0)

def sim(k, p, opp, home, wk):
    n = SIMS
    o = om(p["tm"], wk)
    hm = HFA.get("RB", 1.05)
    hm = hm if home else 1.0 / hm
    rd = dm(opp, "m_ypcar")
    td_d = dm(opp, "m_rutd")

    # backfield share: normalized across the team, and
    # redistributed when a teammate is hurt
    rs = RSM.get(k, {}).get(str(wk), 1.0)
    car = np.random.normal(
        p["tmcar"] * p["cshare"] * rs * (o ** .3),
        max(2.0, p["sd_c"] * .8), n)
    car = np.clip(car, 0, 34)
    ypc = np.random.normal(p["ypc"] * rd * (hm ** .5), 1.5, n)
    ryd = np.clip(car * ypc, -20, 320)

    # tush push: the QB takes goal-line carries, but those
    # teams reach the goal line far more often. Measured net
    # effect on RB rush TDs was +8%, so the penalty is light.
    q = QSH.get(p["tm"], LGQ)
    gl = 1.0 - 0.25 * (q - LGQ)
    rtd = np.random.poisson(
        np.clip(car * p["tdc"] * o * td_d * gl, 0, 4))

    pts = ryd * .1 + rtd * 6
    w = W.get(k)
    if w:
        sm = SM.get(k, {}).get(str(wk), 1.0)
        qn = QNOW.get(p["tm"], 1.0)
        tg = np.clip(np.random.normal(
            w["tmatt"] * w["tshare"] * sm, 1.6, n), 0, 14)
        cr = min(.92, max(.4, w["crate"]))
        rec = np.random.binomial(np.round(tg).astype(int), cr)
        ypr = np.clip(np.random.normal(
            (w["adot"] * FCT + w["yac"]) * qn, 3.4, n), 0, 30)
        ptd = np.random.poisson(
            np.clip(tg * w["tdt"] * o, 0, 3))
        pts = pts + rec + rec * ypr * .1 + ptd * 6
    return pts

OUT = {}
for k, p in R.items():
    if p["tm"] not in SCH:
        continue
    wks = []
    for w in range(CUR, 18):
        m = SCH[p["tm"]].get(w)
        if not m:
            wks.append({"w": w, "o": "BYE", "m": 0.0})
            continue
        s = sim(k, p, m[0], m[1], w)
        out = (RSM.get(k, {}).get(str(w), 1.0) == 0.0
               or SM.get(k, {}).get(str(w), 1.0) == 0.0)
        wks.append({"w": w, "o": m[0], "h": m[1],
                    "out": 1 if out else 0,
                    "m": round(float(s.mean()), 2),
                    "sd": round(float(s.std()), 2),
                    "lo": round(float(np.percentile(s, 10)), 1),
                    "hi": round(float(np.percentile(s, 90)), 1)})
    pl = [x["m"] for x in wks
          if x["o"] != "BYE" and not x.get("out")] or [0.0]
    OUT[k] = {"n": p["n"], "pos": "RB", "tm": p["tm"],
              "ppg": round(float(np.mean(pl)), 2), "wk": wks}
json.dump(OUT, open("site/_rbproj.json", "w"),
          separators=(",", ":"))
print("simulated %d RBs x %d wks x %d sims"
      % (len(OUT), 18 - CUR, SIMS))

r = sorted(OUT.values(), key=lambda x: -x["ppg"])[:22]
print("\n=== RB RANKINGS (20k sims) ===")
print("  %-3s %-24s %-4s %7s %7s %7s"
      % ("#", "PLAYER", "TM", "PPG", "FLOOR", "CEIL"))
for i, v in enumerate(r, 1):
    w = [x for x in v["wk"] if x["o"] != "BYE"
         and not x.get("out")]
    print("  %-3d %-24s %-4s %7.1f %7.1f %7.1f"
          % (i, v["n"][:24], v["tm"], v["ppg"],
             np.mean([x["lo"] for x in w]),
             np.mean([x["hi"] for x in w])))
