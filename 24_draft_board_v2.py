import pandas as pd

REPL = {"QB": 12, "RB": 24, "WR": 36, "TE": 12, "K": 12, "DST": 12}
REL = {"QB": 0.41, "RB": 0.79, "WR": 0.76, "TE": 0.76, "K": 0.05, "DST": 0.30}

p = pd.read_csv("latest_player_projections_v2.csv", low_memory=False)
p = p[p["position"].isin(["QB", "RB", "WR", "TE"])].rename(
    columns={"player_id": "gsis_id", "player_display_name": "name"})

ct = pd.read_csv("rosters_with_rankings.csv", low_memory=False)[["gsis_id", "team"]]
ct = ct.dropna(subset=["gsis_id"]).drop_duplicates("gsis_id").rename(columns={"team": "cur"})
p = p.merge(ct, on="gsis_id", how="left")
p["team"] = p["cur"].fillna(p["team"])

k = pd.read_csv("latest_kicker_projections.csv", low_memory=False)[
    ["player_id", "player_display_name", "team", "final_projection"]].rename(
    columns={"player_id": "gsis_id", "player_display_name": "name"})
k["position"] = "K"

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
allp["vorp"] = allp["final_projection"] - allp["position"].map(rv)
allp["vorp_adj"] = allp["vorp"] * allp["position"].map(REL)

b = allp.sort_values("vorp_adj", ascending=False).reset_index(drop=True)
b["overall_rank"] = b.index + 1

print("--- Draft Board v2: top 50 ---")
print(b[["overall_rank", "name", "position", "team", "final_projection", "vorp", "vorp_adj"]].head(50).to_string(index=False))
print("\nFirst K at rank:", int(b[b["position"] == "K"]["overall_rank"].min()))
print("First DST at rank:", int(b[b["position"] == "DST"]["overall_rank"].min()))

b.to_csv("draft_board_v2.csv", index=False)
print("\nSaved draft_board_v2.csv")
