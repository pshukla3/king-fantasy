import json
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

B0, B1, B2, B3 = 8.829, 0.283, -0.167, 0.653
print("model: %.3f + %.3f*own_prior %.3f*opp_ppg "
      "+ %.3f*home" % (B0, B1, B2, B3))

import os
if os.path.exists("off_ppg_2025.csv"):
    _c = pd.read_csv("off_ppg_2025.csv")
    OPPG = dict(zip(_c["team"], _c["ppg"]))
    print("offense ppg from cache (%d teams)" % len(OPPG))
    P = None
else:
    P = pl(nfl.load_pbp(seasons=[2025]))
if P is not None:
    P = P[["game_id", "home_team", "away_team",
           "home_score", "away_score"]].dropna(
        subset=["home_team", "away_team"])
if P is not None:
    sc = P.groupby(["game_id", "home_team",
                    "away_team"]).agg(
        hs=("home_score", "max"),
        a_s=("away_score", "max")).reset_index()
    off = {}
    for _, r in sc.iterrows():
        off.setdefault(r["home_team"], []).append(r["hs"])
        off.setdefault(r["away_team"], []).append(r["a_s"])
    OPPG = {k: float(np.mean(v)) for k, v in off.items()}
    pd.DataFrame([{"team": k, "ppg": v}
                  for k, v in OPPG.items()]).to_csv(
        "off_ppg_2025.csv", index=False)
    print("cached off_ppg_2025.csv")
print("2025 offense ppg for %d teams (mean %.1f)"
      % (len(OPPG), np.mean(list(OPPG.values()))))

D = pd.read_csv("dst_proj.csv")
OWN = dict(zip(D["team"], D["last_ppg"]))
SCH = json.load(open("site/_sched.json"))["sched"]
NICK = {"BUF":"Bills","MIA":"Dolphins","NE":"Patriots",
 "NYJ":"Jets","BAL":"Ravens","CIN":"Bengals","CLE":"Browns",
 "PIT":"Steelers","HOU":"Texans","IND":"Colts",
 "JAX":"Jaguars","TEN":"Titans","DEN":"Broncos",
 "KC":"Chiefs","LV":"Raiders","LAC":"Chargers",
 "DAL":"Cowboys","NYG":"Giants","PHI":"Eagles",
 "WAS":"Commanders","CHI":"Bears","DET":"Lions",
 "GB":"Packers","MIN":"Vikings","ATL":"Falcons",
 "CAR":"Panthers","NO":"Saints","TB":"Buccaneers",
 "ARI":"Cardinals","LA":"Rams","SF":"49ers",
 "SEA":"Seahawks"}
LOGO = ("https://a.espncdn.com/i/teamlogos/nfl/500/%s.png")
FIX = {"LA": "lar", "WAS": "wsh"}
mu = float(np.mean(list(OPPG.values())))

OUT, ROWS = {}, []
for t in NICK:
    own = OWN.get(t)
    if own is None:
        continue
    wk = SCH.get(t, {})
    weeks, tot = {}, []
    for w, d in wk.items():
        o = d.get("o")
        home = 1 if d.get("at") == "vs" else 0
        oppg = OPPG.get(o, mu)
        v = B0 + B1 * own + B2 * oppg + B3 * home
        weeks[str(w)] = round(float(v), 2)
        tot.append(v)
    if not tot:
        continue
    avg = float(np.mean(tot))
    ab = FIX.get(t, t.lower())
    OUT[t] = {"nm": NICK[t] + " Defense", "tm": t,
              "logo": LOGO % ab, "ppg": round(avg, 2),
              "own_prior": round(float(own), 2),
              "wk": weeks}
    ROWS.append({"player_display_name": NICK[t] + " Defense",
                 "position": "DST", "team": t,
                 "points": round(avg, 2)})
json.dump(OUT, open("site/_dst.json", "w"))
print("\nwrote site/_dst.json: %d defenses" % len(OUT))

R = pd.DataFrame(ROWS).sort_values("points",
                                   ascending=False)
print("\n=== 2026 SEASON PROJECTIONS ===")
print(R.head(8).to_string(index=False))
print("  ...")
print(R.tail(5).to_string(index=False))
print("\n  spread top to bottom: %.2f ppg"
      % (R["points"].max() - R["points"].min()))
print("  weekly MAE is 4.49, so that entire spread is")
print("  about a third of one week's error. Streaming on")
print("  matchup beats holding a 'good' defense.")

best = max(OUT.items(), key=lambda x: x[1]["ppg"])
t, v = best
ws = sorted(v["wk"].items(), key=lambda x: -x[1])[:3]
print("\n  %s best weeks: %s"
      % (v["nm"], ", ".join("wk%s %.1f" % (a, b)
                            for a, b in ws)))
ws = sorted(v["wk"].items(), key=lambda x: x[1])[:3]
print("  %s worst weeks: %s"
      % (v["nm"], ", ".join("wk%s %.1f" % (a, b)
                            for a, b in ws)))

import os
if os.path.exists("dst_quant.csv"):
    _q = pd.read_csv("dst_quant.csv")
    Q10, Q50, Q90 = (float(_q["q10"][0]), float(_q["q50"][0]),
                     float(_q["q90"][0]))
    print("dst quantiles from cache")
else:
    _p = pl(nfl.load_pbp(seasons=[2025]))
    _d = _p[_p["defteam"].notna()]
    for _c in ["sack", "interception", "fumble_lost",
               "touchdown", "safety", "home_score",
               "away_score"]:
        _p[_c] = pd.to_numeric(_p[_c],
                               errors="coerce").fillna(0)
        _d[_c] = pd.to_numeric(_d[_c],
                               errors="coerce").fillna(0)
    _g = _d.groupby(["game_id", "defteam"]).agg(
        sk=("sack", "sum"), ic=("interception", "sum"),
        fu=("fumble_lost", "sum"),
        sf=("safety", "sum")).reset_index()
    _sc = _p.groupby(["game_id", "home_team",
                      "away_team"]).agg(
        hs=("home_score", "max"),
        a_s=("away_score", "max")).reset_index()
    _pa = {}
    for _, r in _sc.iterrows():
        _pa[(r["game_id"], r["home_team"])] = r["a_s"]
        _pa[(r["game_id"], r["away_team"])] = r["hs"]
    _g["pa"] = [_pa.get((a2, b2), np.nan) for a2, b2 in
                zip(_g["game_id"], _g["defteam"])]

    def _pap(x):
        if x != x:
            return 0
        return (10 if x == 0 else 7 if x <= 6 else 4
                if x <= 13 else 1 if x <= 20 else 0
                if x <= 27 else -1 if x <= 34 else -4)
    _g["fp"] = (_g["sk"] + 2 * _g["ic"] + 2 * _g["fu"]
                + 2 * _g["sf"] + _g["pa"].map(_pap))
    _m = _g["fp"].mean()
    Q10, Q50, Q90 = [float(np.percentile(_g["fp"], p) / _m)
                     for p in (10, 50, 90)]
    pd.DataFrame([{"q10": Q10, "q50": Q50,
                   "q90": Q90}]).to_csv("dst_quant.csv",
                                        index=False)
    print("dst weekly ratios: p10 %.2f p50 %.2f p90 %.2f"
          % (Q10, Q50, Q90))

BF = pd.read_csv("board_final.csv")
BF = BF[BF["position"] != "DST"]
add = []
for t, v in OUT.items():
    g0 = v["ppg"]
    add.append({"player_id": "DST_" + t,
                "player_display_name": v["nm"],
                "position": "DST", "team": t,
                "points": g0, "source": "dst_model",
                "points_mult": 1.0, "games_mult": 1.0,
                "exp_games": 17, "status": "",
                "p10": round(g0 * Q10, 2),
                "p50": round(g0 * Q50, 2),
                "p90": round(g0 * Q90, 2)})
BF = pd.concat([BF, pd.DataFrame(add)], ignore_index=True)
BF.to_csv("board_final.csv", index=False)
print("\nboard: DST rows now %d (was 11)"
      % int((BF["position"] == "DST").sum()))
