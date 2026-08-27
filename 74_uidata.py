import pandas as pd, numpy as np, json, re
import nflreadpy as nfl

def grab(fn, **kw):
    try:
        d = getattr(nfl, fn)(**kw)
        return d.to_pandas() if hasattr(d, "to_pandas") else d
    except Exception as e:
        print("  %s failed: %s" % (fn, str(e)[:70]))
        return None

D = pd.read_csv("depth_latest.csv", low_memory=False)
D["pos_rank"] = pd.to_numeric(D["pos_rank"], errors="coerce")
D["espn_id"] = D["espn_id"].astype("Int64").astype(str).replace("<NA>", "")
print("depth chart rows: %d | teams: %d | groups: %s"
      % (len(D), D["team"].nunique(), sorted(D["pos_grp"].dropna().unique())))

def side(g):
    g = str(g)
    if "WR" in g or "TE" in g:
        return "offense"
    if "Special" in g:
        return "special"
    return "defense"
D["side"] = D["pos_grp"].map(side)
print("  offense %d | defense %d | special %d"
      % ((D.side == "offense").sum(), (D.side == "defense").sum(), (D.side == "special").sum()))

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
AC = next((c for c in ["attempts", "pass_attempts"] if c in H.columns), None)
OC = next((c for c in ["opponent_team", "opponent"] if c in H.columns), None)
for c in ["carries", "targets", "receptions", "rushing_yards", "rushing_tds",
          "receiving_yards", "receiving_tds", "passing_yards", "passing_tds",
          "interceptions"]:
    if c not in H.columns:
        H[c] = 0.0
    H[c] = H[c].fillna(0.0)
H["att"] = H[AC].fillna(0.0) if AC else 0.0
H["pts"] = (H["rushing_yards"] * 0.1 + H["rushing_tds"] * 6 + H["receptions"]
            + H["receiving_yards"] * 0.1 + H["receiving_tds"] * 6
            + H["passing_yards"] * 0.04 + H["passing_tds"] * 4
            - H["interceptions"] * 2)
H["td"] = H["rushing_tds"] + H["receiving_tds"] + H["passing_tds"]
H["opp_"] = H["carries"] + H["targets"] + H["att"]

Q = H[H["position"] == "QB"].groupby(["player_id", "team" if "team" in H.columns
     else "recent_team", "season"]).agg(g=("week", "nunique"),
     opp=("opp_", "sum")).reset_index()
Q.columns = ["player_id", "tm", "season", "g", "opp"]
Q["rank"] = Q.groupby(["tm", "season"])["opp"].rank(ascending=False, method="first")
QG = Q[Q["rank"] <= 4].groupby("rank")["g"].agg(["mean", "median", "size"])
print("\n=== MEASURED: GAMES PLAYED BY QB DEPTH RANK ===")
print("  this is why a backup QB projects to nothing")
for r, row in QG.iterrows():
    print("  QB%d   mean %4.1f games   median %4.1f   n=%d"
          % (r, row["mean"], row["median"], row["size"]))
QGAMES = {int(r): float(QG.loc[r, "mean"]) for r in QG.index}

R = grab("load_rosters", seasons=[2026])
HEAD = {}
if R is not None:
    for c in ["headshot_url", "headshot", "espn_headshot"]:
        if c in R.columns:
            for _, r in R.dropna(subset=["gsis_id"]).iterrows():
                if isinstance(r.get(c), str) and r[c].startswith("http"):
                    HEAD[r["gsis_id"]] = r[c]
            break
print("\nheadshots from rosters: %d" % len(HEAD))

def shot(gid, eid):
    if gid in HEAD:
        return HEAD[gid]
    if eid and eid.isdigit():
        return "https://a.espncdn.com/i/headshots/nfl/players/full/%s.png" % eid
    return ""

INJ = grab("load_injuries", seasons=[2026])
if INJ is not None and len(INJ):
    INJ = INJ.sort_values("week").groupby("gsis_id").tail(1)
    print("2026 injury reports: %d players" % len(INJ))
else:
    INJ = pd.DataFrame(columns=["gsis_id", "team", "full_name", "position",
                                "report_status", "report_primary_injury"])
    print("2026 injury feed empty (normal in August) - UI falls back to news_overrides_v2.csv")

import os
if not os.path.exists("coaching_2026.csv"):
    pd.DataFrame({"team": sorted(D["team"].unique()), "head_coach": "",
                  "off_coordinator": "", "def_coordinator": "",
                  "scheme_note": ""}).to_csv("coaching_2026.csv", index=False)
    print("created coaching_2026.csv - fill this in, the UI reads it")
CO = pd.read_csv("coaching_2026.csv").fillna("")

W = H[H["season"] >= 2024].copy()
tmc = "team" if "team" in W.columns else "recent_team"
PLAYERS = {}
for pid, x in W.groupby("player_id"):
    x = x.sort_values(["season", "week"])
    p = x["pts"].values
    if len(p) < 4:
        continue
    PLAYERS[pid] = {
        "games": int(len(p)),
        "ppg": round(float(p.mean()), 2),
        "med": round(float(np.median(p)), 2),
        "p25": round(float(np.percentile(p, 25)), 2),
        "p75": round(float(np.percentile(p, 75)), 2),
        "p90": round(float(np.percentile(p, 90)), 2),
        "hi": round(float(p.max()), 2),
        "sd": round(float(p.std()), 2),
        "p_td": round(float((x["td"] > 0).mean()), 3),
        "p10": round(float((p >= 10).mean()), 3),
        "p15": round(float((p >= 15).mean()), 3),
        "p20": round(float((p >= 20).mean()), 3),
        "log": [{"s": int(a), "w": int(b), "o": (str(c) if OC else ""),
                 "p": round(float(e), 1)}
                for a, b, c, e in zip(x["season"], x["week"],
                                      x[OC] if OC else x["season"], x["pts"])][-40:],
    }
print("players with weekly distributions: %d" % len(PLAYERS))

PROJ = {}
try:
    BD = pd.read_csv("board_situational.csv", low_memory=False)
    for _, r in BD.iterrows():
        PROJ[r["player_id"]] = {"proj": round(float(r.get("proj", 0)), 2),
                                "vorp": round(float(r.get("vorp", 0)), 2),
                                "value": round(float(r.get("value", 0)), 1),
                                "rank": int(r.get("rk", 0))}
except Exception as e:
    print("board_situational.csv not read: %s" % str(e)[:60])

OUT = {"teams": {}, "players": {}}
for tm, x in D.groupby("team"):
    c = CO[CO["team"] == tm]
    OUT["teams"][tm] = {
        "coach": ({k: c.iloc[0][k] for k in
                   ["head_coach", "off_coordinator", "def_coordinator", "scheme_note"]}
                  if len(c) else {}),
        "depth": {},
        "injuries": [],
    }
    for sd in ["offense", "defense", "special"]:
        grp = {}
        for pos, y in x[x["side"] == sd].groupby("pos_abb"):
            grp[pos] = [{"id": r["gsis_id"], "name": r["player_name"],
                         "rank": int(r["pos_rank"]) if r["pos_rank"] == r["pos_rank"] else 99,
                         "img": shot(r["gsis_id"], r["espn_id"])}
                        for _, r in y.sort_values("pos_rank").iterrows()]
        OUT["teams"][tm]["depth"][sd] = grp
    it = INJ[INJ.get("team", pd.Series(dtype=str)) == tm] if len(INJ) else INJ
    for _, r in it.iterrows():
        OUT["teams"][tm]["injuries"].append(
            {"id": r.get("gsis_id", ""), "name": r.get("full_name", ""),
             "pos": r.get("position", ""), "status": str(r.get("report_status", "")),
             "inj": str(r.get("report_primary_injury", ""))})

for _, r in D.iterrows():
    gid = r["gsis_id"]
    if gid in OUT["players"]:
        continue
    rec = {"name": r["player_name"], "team": r["team"], "pos": r["pos_abb"],
           "rank": int(r["pos_rank"]) if r["pos_rank"] == r["pos_rank"] else 99,
           "img": shot(gid, r["espn_id"])}
    if r["pos_abb"] == "QB":
        rec["exp_games"] = round(QGAMES.get(rec["rank"], 1.0), 1)
    rec.update(PLAYERS.get(gid, {}))
    rec.update(PROJ.get(gid, {}))
    OUT["players"][gid] = rec

with open("ui_data.json", "w") as f:
    json.dump(OUT, f)
print("\nSaved ui_data.json  (%d teams, %d players)"
      % (len(OUT["teams"]), len(OUT["players"])))
print("  next: fill in coaching_2026.csv, then I'll build the HTML")
