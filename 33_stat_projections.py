import pandas as pd

WEIGHTS = {2025: 3, 2024: 2, 2023: 1}
WANT = ["completions", "attempts", "passing_yards", "passing_tds", "passing_interceptions",
        "passing_2pt_conversions", "sack_fumbles_lost", "carries", "rushing_yards",
        "rushing_tds", "rushing_fumbles_lost", "rushing_2pt_conversions", "receptions",
        "targets", "receiving_yards", "receiving_tds", "receiving_fumbles_lost",
        "receiving_2pt_conversions", "special_teams_tds"]

s = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
stats = [c for c in WANT if c in s.columns]
print(f"Stat columns found: {len(stats)} of {len(WANT)}")
print("Missing:", [c for c in WANT if c not in s.columns])

s = s[s["season"].isin(WEIGHTS)]
g = s.groupby(["player_id", "season"])[stats].mean().reset_index()
games = s.groupby(["player_id", "season"]).size().rename("games").reset_index()
g = g.merge(games, on=["player_id", "season"])
g = g[g["games"] >= 4]
g["w"] = g["season"].map(WEIGHTS) * g["games"]

num = g[stats].mul(g["w"], axis=0)
num["player_id"] = g["player_id"]
num = num.groupby("player_id").sum()
den = g.groupby("player_id")["w"].sum()
proj = num.div(den, axis=0).reset_index()

info = s.sort_values(["season", "week"]).groupby("player_id").tail(1)[
    ["player_id", "player_display_name", "position", "team"]]
proj = proj.merge(info, on="player_id", how="left")

rost = pd.read_csv("rosters_2026.csv", low_memory=False)
active = set(rost["gsis_id"].dropna())
proj = proj[proj["player_id"].isin(active)]
ct = rost[["gsis_id", "team"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id").rename(
    columns={"gsis_id": "player_id", "team": "cur"})
proj = proj.merge(ct, on="player_id", how="left")
proj["team"] = proj["cur"].fillna(proj["team"])
proj = proj.drop(columns=["cur"])

proj.to_csv("stat_projections_2026.csv", index=False)
print("\nSaved stat_projections_2026.csv:", proj.shape)
print("\n--- Top 5 WRs by projected receiving yards/game ---")
print(proj[proj["position"] == "WR"].nlargest(5, "receiving_yards")[
    ["player_display_name", "team", "targets", "receptions", "receiving_yards", "receiving_tds"]
].round(2).to_string(index=False))
