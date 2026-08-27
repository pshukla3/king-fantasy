import pandas as pd

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
d = cw[["gsis_id", "draft_year", "draft_ovr", "position"]].dropna(
    subset=["gsis_id", "draft_year", "draft_ovr"])
d = d[d["position"].isin(["QB", "RB", "WR", "TE"])].drop_duplicates("gsis_id")
d = d[(d["draft_year"] >= 2014) & (d["draft_year"] <= 2025)].copy()
print("Drafted skill players 2014-2025 (full population):", len(d))

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
s = H.groupby(["player_id", "season"]).agg(
    ppg=("fantasy_points_ppr", "mean"), games=("week", "size")).reset_index()

d = d.merge(s, left_on=["gsis_id", "draft_year"], right_on=["player_id", "season"], how="left")
d["ppg"] = d["ppg"].fillna(0.0)
d["games"] = d["games"].fillna(0)
d["played"] = d["games"] >= 1
d["starter"] = d["games"] >= 10
print("never appeared as rookies:", (~d["played"]).sum(), f"({(~d['played']).mean():.0%})")

bins = [0, 10, 32, 64, 105, 150, 262]
lab = ["1-10", "11-32", "33-64", "65-105", "106-150", "151+"]
d["bucket"] = pd.cut(d["draft_ovr"], bins=bins, labels=lab)

t = d.groupby(["position", "bucket"], observed=True).agg(
    n=("ppg", "size"),
    pct_played=("played", "mean"),
    pct_10g=("starter", "mean"),
    ppg_expected=("ppg", "mean"),
    ppg_if_played=("ppg", lambda x: x[x > 0].mean())).reset_index()
t = t[t["n"] >= 5]
print("\n=== Rookie outcomes by draft slot — UNCONDITIONAL ===")
print(t.round(2).to_string(index=False))
t.to_csv("rookie_curve_v2.csv", index=False)

rost = pd.read_csv("rosters_2026.csv", low_memory=False)
r = rost[(rost["rookie_year"] == 2026) & rost["position"].isin(["QB", "RB", "WR", "TE"])].copy()
r["bucket"] = pd.cut(r["draft_number"], bins=bins, labels=lab)
r = r.merge(t[["position", "bucket", "ppg_expected", "pct_10g", "n"]],
            on=["position", "bucket"], how="left")
r["ppg_expected"] = r["ppg_expected"].fillna(0.0)
r["pct_10g"] = r["pct_10g"].fillna(0.0)

print("\n=== 2026 rookies: unconditional expected PPG ===")
print(r.nlargest(20, "ppg_expected")[
    ["full_name", "position", "team", "draft_number", "bucket", "ppg_expected", "pct_10g"]
].round(2).to_string(index=False))
r.to_csv("rookie_projections_2026.csv", index=False)
print("\nundrafted 2026 rookies set to 0.0:", (r["draft_number"].isna()).sum())
