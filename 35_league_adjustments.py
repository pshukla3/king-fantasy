import pandas as pd

STAT_MAP = {
    "pass_yd": ["passing_yards"], "pass_td": ["passing_tds"],
    "pass_int": ["passing_interceptions"], "pass_2pt": ["passing_2pt_conversions"],
    "pass_cmp": ["completions"], "pass_att": ["attempts"],
    "rush_yd": ["rushing_yards"], "rush_td": ["rushing_tds"],
    "rush_2pt": ["rushing_2pt_conversions"], "rush_att": ["carries"],
    "rec": ["receptions"], "rec_yd": ["receiving_yards"], "rec_td": ["receiving_tds"],
    "rec_2pt": ["receiving_2pt_conversions"], "rec_tgt": ["targets"],
    "fum_lost": ["sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost"],
    "st_td": ["special_teams_tds"],
}

def score_frame(df, scoring):
    pts = pd.Series(0.0, index=df.index)
    for k, v in scoring.items():
        cols = [c for c in STAT_MAP.get(k, []) if c in df.columns]
        if cols:
            pts += df[cols].sum(axis=1) * v
    return pts

def season_table(hist, scoring, min_games=8):
    h = hist.copy()
    h["pts"] = score_frame(h, scoring)
    g = h.groupby(["player_id", "position", "season"])["pts"].agg(ppg="mean", games="count").reset_index()
    return g[g["games"] >= min_games]

def pairs(g):
    n = g[["player_id", "season", "ppg"]].copy()
    n["season"] -= 1
    n = n.rename(columns={"ppg": "ppg_next"})
    return g.merge(n, on=["player_id", "season"], how="inner")

hist = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
birth = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]]
birth = birth.dropna().drop_duplicates("gsis_id")

SCORING = {
    "A_fullPPR_4ptTD": {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1,
                        "rush_td": 6, "rec": 1.0, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2},
    "B_halfPPR_6ptTD": {"pass_yd": 0.04, "pass_td": 6, "pass_int": -2, "rush_yd": 0.1,
                        "rush_td": 6, "rec": 0.5, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2},
}

for name, sc in SCORING.items():
    g = season_table(hist, sc)
    d = pairs(g)
    rel = {p: round(x["ppg"].corr(x["ppg_next"]), 3)
           for p, x in d.groupby("position") if len(x) >= 30}
    print(f"\n=== {name} ===")
    print("reliability:", {k: rel[k] for k in ["QB", "RB", "WR", "TE"] if k in rel})

    dd = d.merge(birth, left_on="player_id", right_on="gsis_id", how="inner")
    dd["age"] = dd["season"] - pd.to_datetime(dd["birthdate"], errors="coerce").dt.year
    t = dd.groupby(["position", "age"]).agg(a=("ppg", "sum"), b=("ppg_next", "sum"),
                                            n=("ppg", "size")).reset_index()
    t = t[(t["n"] >= 8) & (t["age"].between(21, 35))]
    t["mult"] = t["b"] / t["a"]
    t["mult"] = t.groupby("position")["mult"].transform(
        lambda s: s.rolling(3, center=True, min_periods=1).mean())
    t.to_csv(f"age_mult_{name}.csv", index=False)
    print(t[t["position"].isin(["RB", "WR"])][["position", "age", "mult", "n"]].round(3).to_string(index=False))
