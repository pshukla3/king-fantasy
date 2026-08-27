import pandas as pd

cw = pd.read_csv("player_id_crosswalk.csv", low_memory=False)
d = cw[["gsis_id", "draft_year", "draft_ovr", "position"]].dropna(subset=["gsis_id"])
d = d.drop_duplicates("gsis_id")

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
s = H.groupby(["player_id", "season"]).agg(
    ppg=("fantasy_points_ppr", "mean"), games=("week", "size")).reset_index()

s = s.merge(d, left_on="player_id", right_on="gsis_id", how="inner")
rk = s[s["season"] == s["draft_year"]].copy()
rk = rk[rk["position"].isin(["QB", "RB", "WR", "TE"])]
print("Historical rookie seasons found:", len(rk))

bins = [0, 10, 32, 64, 105, 150, 260, 10000]
lab = ["1-10", "11-32", "33-64", "65-105", "106-150", "151-259", "UDFA"]
rk["draft_ovr"] = rk["draft_ovr"].fillna(9999)
rk["bucket"] = pd.cut(rk["draft_ovr"], bins=bins, labels=lab, right=True)

t = rk.groupby(["position", "bucket"], observed=True).agg(
    n=("ppg", "size"), rookie_ppg=("ppg", "mean"),
    med=("ppg", "median"), hit_rate=("games", lambda g: (g >= 10).mean())).reset_index()
t = t[t["n"] >= 5]
print("\n=== Rookie PPG by draft slot (2014-2025) ===")
print(t.round(2).to_string(index=False))
t.to_csv("rookie_curve.csv", index=False)

rost = pd.read_csv("rosters_2026.csv", low_memory=False)
r26 = rost[(rost["rookie_year"] == 2026) & rost["position"].isin(["QB", "RB", "WR", "TE"])].copy()
r26["draft_ovr"] = r26["draft_number"].fillna(9999)
r26["bucket"] = pd.cut(r26["draft_ovr"], bins=bins, labels=lab, right=True)
r26 = r26.merge(t[["position", "bucket", "rookie_ppg", "hit_rate", "n"]],
                on=["position", "bucket"], how="left")

print("\n=== 2026 rookies: projected PPG from draft capital ===")
out = r26[["full_name", "position", "team", "draft_number", "bucket", "rookie_ppg", "hit_rate"]]
print(out.dropna(subset=["rookie_ppg"]).nlargest(25, "rookie_ppg").round(2).to_string(index=False))
r26.to_csv("rookie_projections_2026.csv", index=False)
print("\nSaved rookie_curve.csv and rookie_projections_2026.csv")
