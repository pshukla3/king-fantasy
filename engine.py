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
FLEX_ELIGIBLE = {"FLEX": ["RB", "WR", "TE"], "WRRB_FLEX": ["RB", "WR"],
                 "REC_FLEX": ["WR", "TE"], "SUPER_FLEX": ["QB", "RB", "WR", "TE"]}
BENCH = {"BN", "IR", "TAXI"}
SKILL = ["QB", "RB", "WR", "TE"]

def score(df, scoring):
    pts = pd.Series(0.0, index=df.index)
    for k, v in scoring.items():
        cols = [c for c in STAT_MAP.get(k, []) if c in df.columns]
        if cols:
            pts += df[cols].sum(axis=1) * v
    return pts

def _pairs(hist, scoring, min_games=8):
    h = hist.copy()
    h["pts"] = score(h, scoring)
    g = h.groupby(["player_id", "position", "season"])["pts"].agg(ppg="mean", games="count").reset_index()
    g = g[(g["games"] >= min_games) & (g["position"].isin(SKILL))]
    n = g[["player_id", "season", "ppg"]].copy()
    n["season"] -= 1
    n = n.rename(columns={"ppg": "ppg_next"})
    return g.merge(n, on=["player_id", "season"], how="inner")

def reliability(hist, scoring):
    d = _pairs(hist, scoring)
    return {p: float(x["ppg"].corr(x["ppg_next"]))
            for p, x in d.groupby("position") if len(x) >= 30 and x["ppg"].std() > 0}

def age_curve(hist, scoring, birth):
    d = _pairs(hist, scoring).merge(birth, left_on="player_id", right_on="gsis_id", how="inner")
    d["age"] = d["season"] - pd.to_datetime(d["birthdate"], errors="coerce").dt.year
    t = d.groupby(["position", "age"]).agg(a=("ppg", "sum"), b=("ppg_next", "sum"), n=("ppg", "size")).reset_index()
    t = t[(t["n"] >= 8) & (t["age"].between(20, 38))].copy()
    t["mult"] = t["b"] / t["a"]
    t["mult"] = t.groupby("position")["mult"].transform(lambda s: s.rolling(3, center=True, min_periods=1).mean())
    out = []
    for pos, gp in t.groupby("position"):
        f = pd.DataFrame({"age_prev": range(20, 41)})
        f["position"] = pos
        f = f.merge(gp[["age", "mult"]].rename(columns={"age": "age_prev"}), on="age_prev", how="left")
        f["mult"] = f["mult"].ffill().bfill()
        out.append(f)
    return pd.concat(out, ignore_index=True)

def replacement(df, roster_positions, teams):
    ded, flex = {}, {}
    for s in roster_positions:
        if s in BENCH:
            continue
        tgt = flex if s in FLEX_ELIGIBLE else ded
        tgt[s] = tgt.get(s, 0) + 1
    d = df.sort_values("points", ascending=False).copy()
    d["starter"] = False
    for pos, c in ded.items():
        d.loc[d[(d["position"] == pos) & (~d["starter"])].head(c * teams).index, "starter"] = True
    for s, c in flex.items():
        d.loc[d[(d["position"].isin(FLEX_ELIGIBLE[s])) & (~d["starter"])].head(c * teams).index, "starter"] = True
    repl = {}
    for pos in d["position"].unique():
        ns = d[(d["position"] == pos) & (~d["starter"])]
        repl[pos] = float(ns["points"].max()) if len(ns) else 0.0
    return repl

def build_board(proj, league, hist, birth, season=2026):
    rel = reliability(hist, league["scoring"])
    ages = age_curve(hist, league["scoring"], birth)
    d = proj[proj["position"].isin(SKILL)].copy()
    d["raw_points"] = score(d, league["scoring"])
    d = d.merge(birth, left_on="player_id", right_on="gsis_id", how="left")
    d["age"] = season - pd.to_datetime(d["birthdate"], errors="coerce").dt.year
    d["age_prev"] = d["age"] - 1
    d = d.merge(ages, on=["position", "age_prev"], how="left")
    d["mult"] = d["mult"].fillna(1.0)
    d["points"] = d["raw_points"] * d["mult"]
    repl = replacement(d, league["roster_positions"], league["teams"])
    d["repl"] = d["position"].map(repl)
    d["vorp"] = d["points"] - d["repl"]
    d["reliability"] = d["position"].map(rel).fillna(0.5)
    d["value"] = d["vorp"] * d["reliability"]
    d = d.sort_values("value", ascending=False).reset_index(drop=True)
    d["overall_rank"] = d.index + 1
    d["pos_rank"] = d.groupby("position")["value"].rank(ascending=False, method="min").astype(int)
    return d, rel, repl
