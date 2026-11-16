import glob, re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W = W[W["position"].isin(["QB", "RB", "WR", "TE"])].copy()
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W = W[W["week"] <= 18].sort_values(
    ["k", "season", "week"])
print("base rows: %d | seasons %s-%s"
      % (len(W), W.season.min(), W.season.max()))

print("\n=== WHAT COLUMNS DO WE HAVE? ===")
want = ["targets", "carries", "receptions",
        "receiving_yards", "rushing_yards",
        "passing_yards", "attempts", "completions",
        "target_share", "air_yards_share",
        "receiving_air_yards", "wopr",
        "racr", "pacr", "rushing_tds", "receiving_tds",
        "passing_tds", "opponent_team", "team"]
have = [c for c in want if c in W.columns]
miss = [c for c in want if c not in W.columns]
print("have:", have)
print("MISSING:", miss)

for c in have:
    if c not in ("team", "opponent_team"):
        W[c] = pd.to_numeric(W[c], errors="coerce")\
            .fillna(0.0)

S = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_usage/snaps_2*.parquet"))],
              ignore_index=True)
S["k"] = S["player"].map(norm)
S["snap"] = pd.to_numeric(S["offense_pct"],
                          errors="coerce")
S = S[["season", "week", "k", "snap"]].dropna()
print("\nsnap rows: %d" % len(S))

D = W.merge(S, on=["season", "week", "k"], how="left")
print("snap coverage on merged rows: %.0f%%"
      % (100 * D["snap"].notna().mean()))

# team pass/rush volume per game -> shares
tm = D.groupby(["season", "week", "team"]).agg(
    tm_tgt=("targets", "sum"),
    tm_car=("carries", "sum")).reset_index()
D = D.merge(tm, on=["season", "week", "team"], how="left")
D["tgt_share"] = D["targets"] / D["tm_tgt"].clip(lower=1)
D["car_share"] = D["carries"] / D["tm_car"].clip(lower=1)

# rolling form, strictly backward looking
g = D.groupby(["k", "season"])
for col, out in (("fp", "r3_fp"), ("targets", "r3_tgt"),
                 ("carries", "r3_car"),
                 ("snap", "r3_snap"),
                 ("tgt_share", "r3_tgts"),
                 ("car_share", "r3_cars")):
    D[out] = g[col].transform(
        lambda x: x.shift(1).rolling(3, min_periods=1).mean())
for col, out in (("fp", "r8_fp"), ("snap", "r8_snap")):
    D[out] = g[col].transform(
        lambda x: x.shift(1).rolling(8, min_periods=2).mean())
D["prev_fp"] = g["fp"].shift(1)
D["gm_no"] = g.cumcount()

# last season baseline
prev = (D.groupby(["season", "k"])["fp"].mean()
        .reset_index().rename(columns={"fp": "py_fp"}))
prev["season"] = prev["season"] + 1
D = D.merge(prev, on=["season", "k"], how="left")

# opponent strength: points allowed to the position,
# computed only from prior weeks that season
D = D.sort_values(["season", "week"])
opp = (D.groupby(["season", "week", "opponent_team",
                  "position"])["fp"].sum().reset_index()
       .rename(columns={"fp": "allowed"}))
opp = opp.sort_values(["season", "opponent_team",
                       "position", "week"])
opp["opp_allow"] = (opp.groupby(
    ["season", "opponent_team", "position"])["allowed"]
    .transform(lambda x: x.shift(1).expanding().mean()))
D = D.merge(opp[["season", "week", "opponent_team",
                 "position", "opp_allow"]],
            on=["season", "week", "opponent_team",
                "position"], how="left")

D["is_home"] = 0
D.to_parquet("features.parquet")
FE = ["r3_fp", "r8_fp", "prev_fp", "py_fp", "r3_tgt",
      "r3_car", "r3_snap", "r3_tgts", "r3_cars",
      "r8_snap", "opp_allow", "gm_no"]
print("\n=== FEATURE COVERAGE ===")
for c in FE:
    print("  %-12s %5.0f%% non-null  mean %8.3f"
          % (c, 100 * D[c].notna().mean(), D[c].mean()))
print("\nwrote features.parquet (%d rows, %d features)"
      % (len(D), len(FE)))
