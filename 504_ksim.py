import json, re, datetime
import numpy as np
import nflreadpy as nfl

SIMS = 20000
np.random.seed(23)
BANDS = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))

K = json.load(open("kparams.json"))
OPP = json.load(open("kickopp.json"))
TT = json.load(open("teamtotal.json"))
try:
    INJ = json.load(open("site/_injtime.json"))
except Exception:
    INJ = {}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

LGF = OPP["lg_fga"]
LGD = float(np.mean([v["fga_g"] for v in OPP["def"].values()]))
LGT = TT["lg"]

# league band shares + make rates, from the params build
d = nfl.load_player_stats(list(range(2017, 2027))).to_pandas()
d = d[d["position"] == "K"]
SH, LG = {}, {}
tot = 0.0
for b in BANDS:
    m = float(d["fg_made_" + b].fillna(0).sum())
    a = m + float(d["fg_missed_" + b].fillna(0).sum())
    LG[b] = m / a if a else 0.0
    SH[b] = a
    tot += a
SH = {b: SH[b] / tot for b in BANDS}
LG_TD = 2.272        # league TD/gm (2025 measured)
# walk-forward on 4,481 kicker-games (2018-26) found the
# model under-projects by 0.65 pts. 1.09 zeroes the bias
# and gives the best RMSE (4.481 vs 4.599 league-average).
CAL = 1.09

sc = nfl.load_schedules([2026]).to_pandas()
SCH = {}
for _, g in sc.iterrows():
    w = int(g["week"])
    SCH.setdefault(g["home_team"], {})[w] = (g["away_team"], 1)
    SCH.setdefault(g["away_team"], {})[w] = (g["home_team"], 0)

def sim(p, opp, wk):
    n = SIMS
    tm = p["tm"]
    # FG attempts: team rate shrunk HARD to league (year-to-
    # year r ~ 0), then opponent, then a light game-total
    # nudge (implied total -> attempts was only r=.04)
    tf = OPP["off"].get(tm, {}).get("fga_g", LGF)
    base = 0.30 * tf + 0.70 * LGF
    da = OPP["def"].get(opp, {}).get("fga_g", LGD) / LGD
    base *= min(1.25, max(0.80, da))
    imp = TT["wk"].get(tm, {}).get(str(wk)) or \
        TT["avg"].get(tm, LGT)
    base *= min(1.12, max(0.90, 1 + 0.25 * (imp - LGT) / 17.5))
    # binomial(10, mu/10) matches the observed under-
    # dispersion (mean 2.05, var 1.69)
    att = np.random.binomial(10, min(0.95, base / 10.0), n)

    # band mix: league shares tilted by his 50+ share
    sh = dict(SH)
    tilt = p["legshare"] - (SH["50_59"] + SH["60_"])
    sh["50_59"] += tilt * 0.70
    sh["40_49"] -= tilt * 0.40
    sh["30_39"] -= tilt * 0.30
    ssum = sum(max(1e-6, v) for v in sh.values())
    sh = {b: max(1e-6, sh[b]) / ssum for b in BANDS}

    made = {b: np.zeros(n) for b in BANDS}
    amt = {b: np.zeros(n) for b in BANDS}
    probs = [sh[b] for b in BANDS]
    draw = np.random.multinomial(1, probs, size=(n, 10))
    for i, b in enumerate(BANDS):
        cnt = (draw[:, :, i].cumsum(axis=1)
               * (np.arange(10) < att[:, None])).max(axis=1)
        amt[b] = cnt
        made[b] = np.random.binomial(cnt.astype(int),
                                     p["rate"][b])
    # XPs follow touchdowns, which DO track the game total
    tdr = LG_TD * min(1.30, max(0.75,
                                1 + 0.9 * (imp - LGT) / 17.5))
    att = np.minimum(10, np.round(att * CAL)).astype(int)
    xpa = np.random.poisson(max(0.1, tdr), n)
    xpm = np.random.binomial(xpa, p["xp"])
    return amt, made, xpa, xpm

DFL = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
       "50_59": 5, "60_": 5}

def spread(amt, made, xpa, xpm):
    """per-sim points under default scoring -> floor/ceil"""
    pts = xpm.astype(float)
    for b in BANDS:
        pts = pts + made[b] * DFL[b] - (amt[b] - made[b])
    return (round(float(np.percentile(pts, 10)), 1),
            round(float(np.percentile(pts, 90)), 1),
            round(float(pts.std()), 2))

DFL = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
       "50_59": 5, "60_": 5}

def spread(amt, made, xpa, xpm):
    """per-sim points under default scoring -> floor/ceil"""
    pts = xpm.astype(float)
    for b in BANDS:
        pts = pts + made[b] * DFL[b] - (amt[b] - made[b])
    return (round(float(np.percentile(pts, 10)), 1),
            round(float(np.percentile(pts, 90)), 1),
            round(float(pts.std()), 2))

def line(amt, made, xpa, xpm):
    o = {}
    for b in BANDS:
        o["a_" + b] = round(float(amt[b].mean()), 3)
        o["m_" + b] = round(float(made[b].mean()), 3)
    o["xa"] = round(float(xpa.mean()), 3)
    o["xm"] = round(float(xpm.mean()), 3)
    return o

OUT = {}
for k, p in K.items():
    if not p.get("starter") or p["tm"] not in SCH:
        continue
    v = INJ.get(k)
    miss = (99 if v and v["weeks"] >= 99
            else (v["weeks"] if v else 0))
    wks = []
    for w in range(CUR, 18):
        m = SCH[p["tm"]].get(w)
        if not m:
            wks.append({"w": w, "o": "BYE"})
            continue
        out = miss >= 99 or (miss > 0 and w < CUR + miss)
        a, md, xa, xm = sim(p, m[0], w)
        row = {"w": w, "o": m[0], "h": m[1],
               "out": 1 if out else 0}
        row.update(line(a, md, xa, xm))
        _lo, _hi, _sd = spread(a, md, xa, xm)
        row["lo"], row["hi"], row["sd"] = _lo, _hi, _sd
        _lo, _hi, _sd = spread(a, md, xa, xm)
        row["lo"], row["hi"], row["sd"] = _lo, _hi, _sd
        wks.append(row)
    OUT[k] = {"n": p["n"], "tm": p["tm"], "pos": "K",
              "leg": p["legshare"], "wk": wks}
json.dump(OUT, open("site/_kproj.json", "w"),
          separators=(",", ":"))
print("simulated %d starting kickers x %d wks x %d sims"
      % (len(OUT), 18 - CUR, SIMS))

def score(r, S):
    if r.get("out") or r["o"] == "BYE":
        return 0.0
    t = 0.0
    for b in BANDS:
        key = ("fgm_50p" if b in ("50_59", "60_")
               else "fgm_" + b)
        t += r["m_" + b] * S.get(key, S.get("fgm_" + b, 3))
        t += (r["a_" + b] - r["m_" + b]) * S.get("fgmiss", -1)
    t += r["xm"] * S.get("xpm", 1)
    t += (r["xa"] - r["xm"]) * S.get("xpmiss", 0)
    return t

DEF = {"fgm_0_19": 3, "fgm_20_29": 3, "fgm_30_39": 3,
       "fgm_40_49": 4, "fgm_50p": 5, "fgmiss": -1,
       "xpm": 1, "xpmiss": 0}
MINE = json.load(open("league_scoring.json"))

rows = []
for k, v in OUT.items():
    p = [x for x in v["wk"] if x["o"] != "BYE" and not x.get("out")]
    if not p:
        continue
    rows.append((v["n"], v["tm"], v["leg"],
                 np.mean([score(x, DEF) for x in p]),
                 np.mean([score(x, MINE) for x in p])))
rows.sort(key=lambda x: -x[3])
print("\n%-24s %-4s %7s %9s %11s"
      % ("KICKER", "TM", "50+%", "DEFAULT", "YOUR LEAGUE"))
for r in rows:
    print("%-24s %-4s %6.1f%% %9.2f %11.2f"
          % (r[0][:24], r[1], r[2] * 100, r[3], r[4]))
