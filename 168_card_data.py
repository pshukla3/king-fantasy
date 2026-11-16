import json
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def sv(k):
    return float(V.get(k, 0.0))

B = pd.read_csv("board_final.csv", low_memory=False)
B["player_id"] = B["player_id"].astype(str)
print("board rows %d" % len(B))

P = pl(nfl.load_players())
P["gsis_id"] = P["gsis_id"].astype(str)
P = P.drop_duplicates("gsis_id")
BIO = {}
for _, r in P.iterrows():
    h = r.get("height")
    try:
        h = int(float(h))
        hs = "%d'%d\"" % (h // 12, h % 12)
    except Exception:
        hs = ""
    bd = r.get("birth_date")
    try:
        age = 2026 - int(str(bd)[:4])
    except Exception:
        age = None
    w = r.get("weight")
    try:
        w = int(float(w))
    except Exception:
        w = None
    ex = r.get("years_of_experience")
    try:
        ex = int(float(ex))
    except Exception:
        ex = None
    BIO[r["gsis_id"]] = {
        "age": age, "ht": hs, "wt": w,
        "col": "" if r.get("college_name") != r.get(
            "college_name") else str(r.get("college_name")),
        "exp": ex,
        "jer": r.get("jersey_number"),
        "hs": "" if r.get("headshot") != r.get("headshot")
        else str(r.get("headshot"))}
print("bio entries %d" % len(BIO))

YRS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
W = pl(nfl.load_player_stats(seasons=YRS))
W["player_id"] = W["player_id"].astype(str)
NUM = ["completions", "attempts", "passing_yards",
       "passing_tds", "passing_interceptions",
       "sacks_suffered", "sack_fumbles_lost",
       "carries", "rushing_yards", "rushing_tds",
       "rushing_fumbles_lost", "receptions", "targets",
       "receiving_yards", "receiving_tds",
       "receiving_fumbles_lost"]
for c in NUM:
    if c not in W.columns:
        W[c] = 0.0
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
W = W[W["season_type"] == "REG"] if "season_type" \
    in W.columns else W

def fpts(d):
    return (d["passing_yards"] * sv("pass_yd")
            + d["passing_tds"] * sv("pass_td")
            + d["passing_interceptions"] * sv("pass_int")
            + d["rushing_yards"] * sv("rush_yd")
            + d["rushing_tds"] * sv("rush_td")
            + d["receptions"] * sv("rec")
            + d["receiving_yards"] * sv("rec_yd")
            + d["receiving_tds"] * sv("rec_td")
            + (d["sack_fumbles_lost"]
               + d["rushing_fumbles_lost"]
               + d["receiving_fumbles_lost"])
            * sv("fum_lost"))

W["fp"] = fpts(W)
AGG = {c: "sum" for c in NUM}
AGG["fp"] = "sum"
AGG["week"] = "nunique"
CAR = W.groupby(["player_id", "season"]).agg(
    AGG).reset_index().rename(columns={"week": "gm"})
tm = (W.sort_values(["player_id", "season", "week"])
      .groupby(["player_id", "season"])["team"]
      .last().reset_index())
CAR = CAR.merge(tm, on=["player_id", "season"], how="left")
print("career rows %d | players %d"
      % (len(CAR), CAR["player_id"].nunique()))
S25 = CAR[CAR["season"] == 2025].set_index("player_id")
print("2025 lines: %d" % len(S25))

SP = pd.read_csv("stat_projections_2026.csv")
SP["player_id"] = SP["player_id"].astype(str)
for c in NUM:
    if c not in SP.columns:
        SP[c] = 0.0
    SP[c] = pd.to_numeric(SP[c], errors="coerce").fillna(0)
SP = SP.drop_duplicates("player_id").set_index("player_id")
print("2026 projection lines: %d" % len(SP))

SCH = pl(nfl.load_schedules(seasons=[2026]))
OPP = {}
for _, r in SCH.iterrows():
    w = int(r["week"])
    h = FIX.get(str(r["home_team"]), str(r["home_team"]))
    a = FIX.get(str(r["away_team"]), str(r["away_team"]))
    OPP.setdefault(h, {})[w] = "vs " + a
    OPP.setdefault(a, {})[w] = "@" + h
print("schedule teams %d" % len(OPP))

def line(d, g, m=1.0):
    return {"gm": int(g),
            "cmp": round(float(d["completions"]) * m),
            "att": round(float(d["attempts"]) * m),
            "pyd": round(float(d["passing_yards"]) * m),
            "ptd": round(float(d["passing_tds"]) * m),
            "int": round(float(d["passing_interceptions"]) * m),
            "car": round(float(d["carries"]) * m),
            "ryd": round(float(d["rushing_yards"]) * m),
            "rtd": round(float(d["rushing_tds"]) * m),
            "tar": round(float(d["targets"]) * m),
            "rec": round(float(d["receptions"]) * m),
            "cyd": round(float(d["receiving_yards"]) * m),
            "ctd": round(float(d["receiving_tds"]) * m)}

CARD = {}
for _, r in B.iterrows():
    pid = str(r["player_id"])
    tmc = FIX.get(str(r["team"]), str(r["team"]))
    ppg = r["points"]
    ppg = float(ppg) if ppg == ppg else 0.0
    sched = OPP.get(tmc, {})
    bye = next((w for w in range(1, 19)
                if w not in sched), 0)
    wk = []
    for w in range(1, 19):
        o = sched.get(w)
        wk.append({"w": w, "opp": o if o else "BYE",
                   "proj": 0.0 if o is None
                   else round(ppg, 2)})
    c = {"id": pid,
         "nm": str(r["player_display_name"]),
         "ps": str(r["position"]), "tm": tmc,
         "by": bye,
         "rk": int(r["rank"]) if r["rank"] == r["rank"] else None,
         "prk": int(r["pos_rank"])
         if r["pos_rank"] == r["pos_rank"] else None,
         "ppg": round(ppg, 2),
         "szn": round(ppg * 17, 1),
         "vorp": round(float(r["vorp"]), 2)
         if r["vorp"] == r["vorp"] else None,
         "adp": float(r["adp"]) if r["adp"] == r["adp"]
         else None,
         "st": "" if r["status"] != r["status"]
         else str(r["status"]),
         "wk": wk}
    c.update(BIO.get(pid, {"age": None, "ht": "", "wt": None,
                           "col": "", "exp": None,
                           "jer": None, "hs": ""}))
    if pid in S25.index:
        d = S25.loc[pid]
        c["s25"] = line(d, d["gm"])
        c["fp25"] = round(float(d["fp"]), 1)
    if pid in SP.index:
        c["p26"] = line(SP.loc[pid], 17, 17.0)
    hist = CAR[CAR["player_id"] == pid]
    c["career"] = [
        {"yr": int(h["season"]), "tm": str(h["team"]),
         "gm": int(h["gm"]), "ppr": round(float(h["fp"]), 1),
         **line(h, h["gm"])}
        for _, h in hist.sort_values(
            "season", ascending=False).iterrows()]
    CARD[pid] = c

json.dump(CARD, open("player_cards.json", "w"))
print("\nwrote player_cards.json: %d cards" % len(CARD))
print("  with 2025 line : %d"
      % sum(1 for v in CARD.values() if "s25" in v))
print("  with 2026 proj : %d"
      % sum(1 for v in CARD.values() if "p26" in v))
print("  with headshot  : %d"
      % sum(1 for v in CARD.values() if v.get("hs")))

print("\n=== ACCURACY GATE (verified vs ESPN/NFL.com) ===")
EXP = [("Tee Higgins", "s25", {"tar": 98, "rec": 59,
                               "cyd": 846, "ctd": 11}),
       ("Caleb Williams", "s25", {"att": 568, "cmp": 330,
                                  "pyd": 3942, "ptd": 27,
                                  "int": 7}),
       ("Colston Loveland", "s25", {"tar": 82, "rec": 58,
                                    "cyd": 713, "ctd": 6}),
       ("Davante Adams", "s25", {"tar": 114, "rec": 60,
                                 "cyd": 789, "ctd": 14})]
fails = []
for nm, key, exp in EXP:
    hit = [v for v in CARD.values()
           if v["nm"] == nm and key in v]
    if not hit:
        fails.append("%s: no %s line" % (nm, key))
        print("  %-18s MISSING" % nm)
        continue
    got = hit[0][key]
    bad = {k: (exp[k], got.get(k)) for k in exp
           if got.get(k) != exp[k]}
    print("  %-18s %s"
          % (nm, "OK" if not bad else "MISMATCH %s" % bad))
    if bad:
        fails.append("%s %s" % (nm, bad))
assert not fails, "2025 data does not match ESPN: %s" % fails
print("\nall four match published stats - data is accurate")
