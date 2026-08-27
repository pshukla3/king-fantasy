import pandas as pd

REPL = {"QB": 12, "RB": 24, "WR": 36, "TE": 12, "K": 12, "DST": 12}
REL = {"QB": 0.41, "RB": 0.79, "WR": 0.76, "TE": 0.76, "K": 0.05, "DST": 0.30}

rost = pd.read_csv("rosters_2026.csv", low_memory=False)
active = set(rost["gsis_id"].dropna())
print("Players on 2026 rosters:", len(active))

p = pd.read_csv("latest_player_projections_v3.csv", low_memory=False)
p = p[p["position"].isin(["QB", "RB", "WR", "TE"])].rename(
    columns={"player_id": "gsis_id", "player_display_name": "name"})
before = len(p)
p = p[p["gsis_id"].isin(active)]
print(f"Skill players: {before} -> {len(p)} after roster filter")

ct = rost[["gsis_id", "team"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
ct = ct.rename(columns={"team": "cur"})
p = p.merge(ct, on="gsis_id", how="left")
p["team"] = p["cur"].fillna(p["team"])

k = pd.read_csv("latest_kicker_projections.csv", low_memory=False)[
    ["player_id", "player_display_name", "team", "final_projection"]].rename(
    columns={"player_id": "gsis_id", "player_display_name": "name"})
k["position"] = "K"
k = k[k["gsis_id"].isin(active)]

d = pd.read_csv("latest_team_defense_projections.csv", low_memory=False)[["team", "final_projection"]].copy()
d["name"] = d["team"] + " D/ST"
d["position"] = "DST"
d["gsis_id"] = None

cols = ["gsis_id", "name", "position", "team", "final_projection"]
allp = pd.concat([p[cols], k[cols], d[cols]], ignore_index=True).dropna(subset=["final_projection"])

def repl_val(gr):
    r = REPL.get(gr.name)
    v = gr["final_projection"].sort_values(ascending=False).reset_index(drop=True)
    return v.iloc[-1] if r is None or r > len(v) else v.iloc[r - 1]

rv = allp.groupby("position").apply(repl_val)
print("\nReplacement level after filter:")
print(rv.round(2).to_string())

allp["vorp"] = allp["final_projection"] - allp["position"].map(rv)
allp["vorp_adj"] = allp["vorp"] * allp["position"].map(REL)

b = allp.sort_values("vorp_adj", ascending=False).reset_index(drop=True)
b["overall_rank"] = b.index + 1

print("\n--- Draft Board v3: top 40 ---")
print(b[["overall_rank", "name", "position", "team", "final_projection", "vorp_adj"]].head(40).to_string(index=False))

b.to_csv("draft_board_v3.csv", index=False)
print("\nSaved draft_board_v3.csv")
