import json, re, datetime
import numpy as np
import nflreadpy as nfl

from namekey import nk as norm

Z = lambda d, c: d[c].fillna(0.0).astype(float)
YR = [2025, 2026]
d = nfl.load_player_stats(YR).to_pandas()
KB = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
KCOLS = (["fg_att", "fg_made", "fg_long", "pat_att",
          "pat_made"]
         + ["fg_made_" + b for b in KB]
         + ["fg_missed_" + b for b in KB])
for c in KCOLS:
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)

for c in ("carries", "rushing_yards", "rushing_tds",
          "targets", "receptions", "receiving_yards",
          "receiving_tds", "attempts", "passing_yards",
          "passing_tds", "passing_interceptions",
          "receiving_air_yards"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = Z(d, c)

d["kpts"] = (
        d["fg_made_0_19"] * 3 + d["fg_made_20_29"] * 3
        + d["fg_made_30_39"] * 3 + d["fg_made_40_49"] * 4
        + d["fg_made_50_59"] * 5 + d["fg_made_60_"] * 5
        + d["pat_made"]
        - sum(d["fg_missed_" + b] for b in KB))
d["ppr"] = (d["passing_yards"] * .04 + d["passing_tds"] * 4
            - d["passing_interceptions"]
            + d["rushing_yards"] * .1 + d["rushing_tds"] * 6
            + d["receptions"] + d["receiving_yards"] * .1
            + d["receiving_tds"] * 6)
# kickers score by kicking, not by the PPR formula
d.loc[d["position"] == "K", "ppr"] = d.loc[
    d["position"] == "K", "kpts"]

# team carry share + opponent + snap%
tc = d.groupby(["season", "week", "team"],
               as_index=False)["carries"].sum()
tc = tc.rename(columns={"carries": "tmcar"})
d = d.merge(tc, on=["season", "week", "team"], how="left")

sc = nfl.load_schedules(YR).to_pandas()
OPP = {}
for _, g in sc.iterrows():
    k = (int(g["season"]), int(g["week"]))
    OPP[k + (g["home_team"],)] = (g["away_team"], 1)
    OPP[k + (g["away_team"],)] = (g["home_team"], 0)

try:
    sn = nfl.load_snap_counts(YR).to_pandas()
    sn = sn[["season", "week", "player", "team", "offense_pct"]]
    sn["offense_pct"] = sn["offense_pct"].fillna(0).astype(float)
    if sn["offense_pct"].max() > 1.5:
        sn["offense_pct"] /= 100.0
    d = d.merge(sn, left_on=["season", "week",
                             "player_display_name", "team"],
                right_on=["season", "week", "player", "team"],
                how="left")
except Exception as e:
    print("snaps:", e)
    d["offense_pct"] = np.nan

d = d[d["position"].isin(["QB", "RB", "WR", "TE", "K"])]
print("rows: %d  players: %d"
      % (len(d), d["player_id"].nunique()))

CARD = {}
for pid, g in d.groupby("player_id"):
    g = g.sort_values(["season", "week"])
    nm = g["player_display_name"].iloc[-1]
    logs = []
    for _, r in g.iterrows():
        o = OPP.get((int(r["season"]), int(r["week"]),
                     r["team"]), ("", 0))
        sp = r.get("offense_pct")
        logs.append({
            "s": int(r["season"]), "w": int(r["week"]),
            "o": o[0], "h": o[1],
            "p": round(float(r["ppr"]), 1),
            "sn": (round(float(sp) * 100) if sp == sp else None),
            "ca": int(r["carries"]), "ry": int(r["rushing_yards"]),
            "rt": int(r["rushing_tds"]),
            "cs": (round(r["carries"] / r["tmcar"] * 100)
                   if r["tmcar"] > 0 else 0),
            "ta": int(r["targets"]), "re": int(r["receptions"]),
            "yd": int(r["receiving_yards"]),
            "td": int(r["receiving_tds"]),
            "fa": int(r["fg_att"]), "fm": int(r["fg_made"]),
            "fl": int(r["fg_long"]),
            "xa": int(r["pat_att"]), "xm": int(r["pat_made"]),
            "k5": int(r["fg_made_50_59"] + r["fg_made_60_"]),
            "at": int(r["attempts"]),
            "py": int(r["passing_yards"]),
            "pt": int(r["passing_tds"]),
            "in": int(r["passing_interceptions"]),
        })
    career = []
    for s, gg in g.groupby("season"):
        n = len(gg)
        career.append({
            "s": int(s), "gp": n, "tm": gg["team"].iloc[-1],
            "ppr": round(float(gg["ppr"].mean()), 2),
            "ca": round(float(gg["carries"].mean()), 1),
            "ry": round(float(gg["rushing_yards"].mean()), 1),
            "ypc": round(float(gg["rushing_yards"].sum()
                               / max(1, gg["carries"].sum())), 2),
            "ta": round(float(gg["targets"].mean()), 1),
            "re": round(float(gg["receptions"].mean()), 1),
            "yd": round(float(gg["receiving_yards"].mean()), 1),
            "td": round(float(gg["receiving_tds"].sum()), 0),
            "sn": (round(float(gg["offense_pct"].mean()) * 100)
                   if gg["offense_pct"].notna().any() else None),
        })
    CARD[norm(nm)] = {"n": nm, "pos": g["position"].iloc[-1],
                      "tm": g["team"].iloc[-1],
                      "log": logs, "car": career}

# attach our projections for the rest of the season
# kickers: _kproj holds stat lines, so score them first
try:
    _KB = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
    _KP = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
           "50_59": 5, "60_": 5}
    _K = json.load(open("site/_kproj.json"))
    _n = 0
    for _k, _v in _K.items():
        if _k not in CARD:
            continue
        _wk = []
        for _x in _v["wk"]:
            _r = dict(_x)
            if _x.get("o") != "BYE" and not _x.get("out"):
                _p = _x["xm"]
                for _b in _KB:
                    _p += _x["m_" + _b] * _KP[_b]
                    _p -= (_x["a_" + _b] - _x["m_" + _b])
                _r["m"] = round(_p, 2)
            else:
                _r["m"] = 0.0
            _wk.append(_r)
        _play = [x["m"] for x in _wk
                 if x.get("o") != "BYE" and not x.get("out")]
        CARD[_k]["proj"] = _wk
        CARD[_k]["ppg"] = (round(sum(_play) / len(_play), 2)
                           if _play else 0.0)
        _n += 1
    print("kicker projections attached to %d cards" % _n)
except Exception as _e:
    print("kproj:", _e)

for f in ("site/_wrproj.json", "site/_qbproj.json",
          "site/_rbproj.json"):
    try:
        for k, v in json.load(open(f)).items():
            if k in CARD:
                CARD[k]["proj"] = v["wk"]
                CARD[k]["ppg"] = v["ppg"]
    except Exception as e:
        print(f, e)

# board info: rank, value, injury
try:
    B = json.load(open("site/_board.json"))
    for r in B["rows"]:
        k = norm(r.get("n"))
        if k in CARD:
            CARD[k].update({
                "pid": r.get("pid"),
                "rk": r.get("rk"), "posrk": r.get("posrk"),
                "val": r.get("val"), "adp": r.get("adp"),
                "bye": r.get("bye"), "img": r.get("img"),
                "inj": r.get("inj"),
                "inj_body": r.get("inj_body"),
                "inj_why": r.get("inj_why"),
                "inj_wks": r.get("inj_wks"),
                "live": r.get("live"), "gleft": r.get("gleft"),
            })
except Exception as e:
    print("board:", e)

json.dump(CARD, open("site/_cards.json", "w"),
          separators=(",", ":"))
import os
print("wrote site/_cards.json (%d players, %d KB)"
      % (len(CARD), os.path.getsize("site/_cards.json") // 1024))

# rank history: append today's rank, keep the series
H = {}
try:
    H = json.load(open("site/_rankhist.json"))
except Exception:
    pass
today = datetime.date.today().isoformat()
n = 0
for k, v in CARD.items():
    if v.get("posrk"):
        a = H.setdefault(k, [])
        if not a or a[-1][0] != today:
            a.append([today, v["posrk"]])
            n += 1
        H[k] = a[-60:]
json.dump(H, open("site/_rankhist.json", "w"),
          separators=(",", ":"))
print("rank history: %d players updated" % n)

s = CARD.get("omarion hampton")
if s:
    print("\nsample: %s %s %s  rk %s  ppg %s"
          % (s["n"], s["pos"], s["tm"], s.get("rk"),
             s.get("ppg")))
    print("  logs %d  career %d  proj %d"
          % (len(s["log"]), len(s["car"]),
             len(s.get("proj", []))))
    print("  last game:", json.dumps(s["log"][-1]))
