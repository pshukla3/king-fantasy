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

def score(df, scoring):
    pts = pd.Series(0.0, index=df.index)
    hit, miss = [], []
    for k, v in scoring.items():
        cols = [c for c in STAT_MAP.get(k, []) if c in df.columns]
        if cols:
            pts += df[cols].sum(axis=1) * v
            hit.append(k)
        else:
            miss.append(k)
    return pts, hit, miss

def replacement(df, roster_positions, teams):
    ded, flex = {}, {}
    for s in roster_positions:
        if s in BENCH:
            continue
        if s in FLEX_ELIGIBLE:
            flex[s] = flex.get(s, 0) + 1
        else:
            ded[s] = ded.get(s, 0) + 1
    d = df.sort_values("points", ascending=False).copy()
    d["starter"] = False
    for pos, c in ded.items():
        i = d[(d["position"] == pos) & (~d["starter"])].head(c * teams).index
        d.loc[i, "starter"] = True
    for s, c in flex.items():
        i = d[(d["position"].isin(FLEX_ELIGIBLE[s])) & (~d["starter"])].head(c * teams).index
        d.loc[i, "starter"] = True
    repl = {}
    for pos in d["position"].unique():
        ns = d[(d["position"] == pos) & (~d["starter"])]
        repl[pos] = float(ns["points"].max()) if len(ns) else 0.0
    return repl, d

def build(proj, league):
    df = proj.copy()
    df["points"], hit, miss = score(df, league["scoring"])
    if miss:
        print("  unmapped scoring keys:", miss)
    repl, d = replacement(df, league["roster_positions"], league["teams"])
    d["repl"] = d["position"].map(repl)
    d["vorp"] = d["points"] - d["repl"]
    d = d.sort_values("vorp", ascending=False).reset_index(drop=True)
    d["rank"] = d.index + 1
    return d, repl

proj = pd.read_csv("stat_projections_2026.csv", low_memory=False)
proj = proj[proj["position"].isin(["QB", "RB", "WR", "TE"])]

LEAGUES = {
    "A: 10tm full-PPR, 2 FLEX": {
        "teams": 10,
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"],
        "scoring": {"pass_yd": 0.04, "pass_td": 4, "pass_int": -2, "rush_yd": 0.1,
                    "rush_td": 6, "rec": 1.0, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2},
    },
    "B: 12tm half-PPR, SUPERFLEX": {
        "teams": 12,
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "SUPER_FLEX"],
        "scoring": {"pass_yd": 0.04, "pass_td": 6, "pass_int": -2, "rush_yd": 0.1,
                    "rush_td": 6, "rec": 0.5, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2},
    },
}

out = {}
for name, lg in LEAGUES.items():
    print(f"\n=== {name} ===")
    d, repl = build(proj, lg)
    print("  replacement:", {k: round(v, 2) for k, v in repl.items()})
    print(d[["rank", "player_display_name", "position", "team", "points", "vorp"]].head(15).round(2).to_string(index=False))
    out[name] = d.set_index("player_id")["rank"]

cmp = pd.DataFrame(out)
cmp.columns = ["rank_A", "rank_B"]
cmp["shift"] = cmp["rank_A"] - cmp["rank_B"]
nm = proj.set_index("player_id")[["player_display_name", "position"]]
cmp = cmp.join(nm).dropna()
print("\n--- Biggest risers going from league A to league B ---")
print(cmp.nlargest(10, "shift")[["player_display_name", "position", "rank_A", "rank_B", "shift"]].to_string(index=False))
