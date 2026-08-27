import pandas as pd

d = pd.read_csv("age_deltas.csv", low_memory=False)
t = d.groupby(["position", "age"])["delta"].agg(mean_delta="mean", n="count").reset_index()
t = t[t["n"] >= 8].sort_values(["position", "age"])
t["smooth"] = t.groupby("position")["mean_delta"].transform(
    lambda s: s.rolling(3, center=True, min_periods=1).mean())
t.loc[t["position"] == "QB", "smooth"] = 0.0

print("--- Smoothed aging deltas (QB zeroed: no signal) ---")
print(t[t["position"].isin(["RB", "WR", "TE"])].round(2).to_string(index=False))

grid = []
for pos, grp in t.groupby("position"):
    full = pd.DataFrame({"age": range(20, 41)})
    full["position"] = pos
    full = full.merge(grp[["age", "smooth"]], on="age", how="left")
    full["smooth"] = full["smooth"].ffill().bfill()
    grid.append(full)
grid = pd.concat(grid).rename(columns={"age": "age_prev", "smooth": "age_delta"})

p = pd.read_csv("latest_player_projections_v2.csv", low_memory=False)
cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)[["gsis_id", "birthdate"]]
cw = cw.dropna().drop_duplicates("gsis_id")

p = p.merge(cw, left_on="player_id", right_on="gsis_id", how="left")
p["age_2026"] = 2026 - pd.to_datetime(p["birthdate"], errors="coerce").dt.year
p["age_prev"] = p["age_2026"] - 1

p = p.merge(grid, on=["position", "age_prev"], how="left")
p["age_delta"] = p["age_delta"].fillna(0.0)
p["proj_aged"] = (p["final_projection"] + p["age_delta"]).clip(lower=0)

show = ["player_display_name", "position", "age_2026", "final_projection", "age_delta", "proj_aged"]
print("\n--- Biggest age penalties ---")
print(p.nsmallest(15, "age_delta")[show].round(2).to_string(index=False))

names = ["Christian McCaffrey", "Derrick Henry", "Travis Kelce", "Davante Adams",
         "Tyreek Hill", "George Kittle", "Jahmyr Gibbs", "Puka Nacua"]
print("\n--- Players we flagged ---")
print(p[p["player_display_name"].isin(names)][show].round(2).to_string(index=False))

out = p[["player_id", "player_display_name", "position", "team", "proj_aged"]].rename(
    columns={"proj_aged": "final_projection"})
out.to_csv("latest_player_projections_v3.csv", index=False)
print("\nSaved latest_player_projections_v3.csv")
