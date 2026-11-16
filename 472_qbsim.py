import json, re, datetime
import numpy as np
import nflreadpy as nfl

SIMS = 20000
np.random.seed(11)
_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

QB = json.load(open("qbparams.json"))
HFA = json.load(open("hfa.json"))
TP = json.load(open("tushpush.json"))
DR = json.load(open("site/_defrank.json"))
QSH = TP["qb_share"]
TT = json.load(open("teamtotal.json"))
LGT, SLOPE = TT["lg"], TT["slope"]

def omult(team, wk):
    """team offense strength from Vegas implied total.
    measured: 0.69 fantasy pts per implied point."""
    t = TT["wk"].get(team, {}).get(str(wk))
    if t is None:
        t = TT["avg"].get(team, LGT)
    return 1.0 + SLOPE * (t - LGT) / 17.5
LG_QSH = float(np.mean(list(QSH.values())))

def dmult(team):
    """opponent pass-defense multiplier, tolerant of shape"""
    v = DR.get(team)
    if v is None:
        return 1.0
    if isinstance(v, dict):
        for k in ("pass_mult", "pmult", "pass", "p"):
            if k in v:
                x = float(v[k])
                return x if 0.5 < x < 1.6 else \
                    1 + (16.5 - x) / 16.5 * 0.12
    try:
        x = float(v)
        return x if 0.5 < x < 1.6 else 1.0
    except Exception:
        return 1.0

sc = nfl.load_schedules([2026]).to_pandas()
SCH = {}
for _, g in sc.iterrows():
    w = int(g["week"])
    SCH.setdefault(g["home_team"], {})[w] = (g["away_team"], 1)
    SCH.setdefault(g["away_team"], {})[w] = (g["home_team"], 0)

def sim(p, opp, home, wk=None):
    n = SIMS
    dm = dmult(opp)
    om = omult(p["tm"], wk)
    om = min(1.30, max(0.72, om))
    hm = HFA["QB"] ** (1 if home else -1)
    ef = dm * (hm ** 0.5)

    att = np.random.normal(p["att"], max(3.0, p["sd_att"]), n)
    att = np.clip(att, 8, 60)
    ypa = np.random.normal(
        p["ypa"] * ef * (om ** 0.5), 1.8, n)
    ypa = np.clip(ypa, 2.0, 14.0)
    pyd = att * ypa
    ptd = np.random.poisson(
        np.clip(att * p["ptd"] * ef * om, 0, 6))
    pint = np.random.poisson(np.clip(att * p["int"], 0, 5))

    car = np.random.normal(p["car"], max(1.2, p["sd_car"]), n)
    car = np.clip(car, 0, 25)
    ypc = np.random.normal(p["ypc"], 2.2, n)
    ryd = np.clip(car * ypc, -10, 200)
    # tush push: team's own QB goal-line share drives rush TDs
    qsh = QSH.get(p["tm"], LG_QSH)
    rtd_r = p["rtd"] * (1 + 1.4 * (qsh - LG_QSH))
    rtd = np.random.poisson(
        np.clip(car * rtd_r * om, 0, 4))

    pts = (pyd * 0.04 + ptd * 4 - pint * 1.0
           + ryd * 0.1 + rtd * 6)
    # a backup's expectation is not "worse play" -- it is
    # mostly ZERO, because he does not take the field.
    if not p.get("qb1"):
        pts = pts * 0.10
    return pts

OUT = {}
for key, p in QB.items():
    tm = p["tm"]
    if tm not in SCH:
        continue
    wks = []
    for w in range(CUR, 18):
        m = SCH[tm].get(w)
        if not m:
            wks.append({"w": w, "o": "BYE", "m": 0.0})
            continue
        opp, home = m
        s = sim(p, opp, home, w)
        wks.append({"w": w, "o": opp, "h": home,
                    "m": round(float(s.mean()), 2),
                    "sd": round(float(s.std()), 2),
                    "lo": round(float(np.percentile(s, 10)), 1),
                    "hi": round(float(np.percentile(s, 90)), 1)})
    played = [x["m"] for x in wks if x["o"] != "BYE"]
    OUT[key] = {"n": p["n"], "tm": tm, "qb1": p.get("qb1", 0),
                "ppg": round(float(np.mean(played)), 2),
                "wk": wks}
json.dump(OUT, open("site/_qbproj.json", "w"),
          separators=(",", ":"))
print("simulated %d QBs x %d weeks x %d sims"
      % (len(OUT), 18 - CUR, SIMS))

r = [v for v in OUT.values() if v.get("qb1")]
r = sorted(r, key=lambda x: -x["ppg"])[:20]
print("\n=== NEW QB RANKINGS (%d sims/game) ===" % SIMS)
print("  %-3s %-22s %-4s %7s %7s %7s"
      % ("#", "QB", "TM", "PPG", "FLOOR", "CEIL"))
for i, v in enumerate(r, 1):
    w = [x for x in v["wk"] if x["o"] != "BYE"]
    lo = np.mean([x["lo"] for x in w])
    hi = np.mean([x["hi"] for x in w])
    print("  %-3d %-22s %-4s %7.1f %7.1f %7.1f"
          % (i, v["n"][:22], v["tm"], v["ppg"], lo, hi))
