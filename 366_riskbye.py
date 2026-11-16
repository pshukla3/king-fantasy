import json
import numpy as np
import pandas as pd

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)

# games played per player-season, last 3 seasons
G = (W[W["season"] >= 2023]
     .groupby(["player_display_name", "position",
               "season"])["week"].nunique().reset_index())
G = G.rename(columns={"week": "gp"})
pm = G.groupby("position")["gp"].mean().to_dict()
print("mean games played by position:")
for k, v in sorted(pm.items()):
    print("   %-4s %.1f" % (k, v))

agg = G.groupby(["player_display_name", "position"])["gp"]\
    .agg(["mean", "count"]).reset_index()
K = 2.0  # shrink toward position mean
RISK = {}
for _, r in agg.iterrows():
    base = pm.get(r["position"], 15.0)
    n = r["count"]
    gp = (r["mean"] * n + base * K) / (n + K)
    RISK[r["player_display_name"]] = {
        "gp": round(float(gp), 1),
        "risk": round(float(max(0.0,
                    min(1.0, 1.0 - gp / 17.0))), 3),
        "seasons": int(n)}
print("\nplayers with injury history: %d" % len(RISK))

SCH = json.load(open("site/_sched.json"))["sched"]
BYE = {}
for tm, wks in SCH.items():
    played = set()
    for w in wks:
        try:
            played.add(int(w))
        except ValueError:
            pass
    for w in range(1, 19):
        if w not in played:
            BYE[tm] = w
            break
print("bye weeks found for %d teams" % len(BYE))
print("  sample:", dict(list(BYE.items())[:6]))

B = pd.read_csv("board_final.csv")
B["bye"] = B["team"].map(lambda t: BYE.get(str(t), 0))
B["inj_risk"] = B["player_display_name"].map(
    lambda n: (RISK.get(n) or {}).get("risk"))
B["exp_g"] = B["player_display_name"].map(
    lambda n: (RISK.get(n) or {}).get("gp"))
# no history (rookies) -> position mean
for p, v in pm.items():
    m = (B["position"] == p) & B["exp_g"].isna()
    B.loc[m, "exp_g"] = round(float(v), 1)
    B.loc[m, "inj_risk"] = round(
        float(max(0.0, 1.0 - v / 17.0)), 3)
B.to_csv("board_final.csv", index=False)

print("\ncoverage: bye %d | risk %d | games %d of %d"
      % (int((B["bye"] > 0).sum()),
         int(B["inj_risk"].notna().sum()),
         int(B["exp_g"].notna().sum()), len(B)))
print("\n=== HIGHEST INJURY RISK IN TOP 60 BY VORP ===")
z = B.sort_values("vorp", ascending=False).head(60)
for _, r in z.sort_values("inj_risk",
                          ascending=False).head(10).iterrows():
    print("  %-24s %-4s risk %4.0f%%  exp games %.1f"
          % (r["player_display_name"][:24], r["position"],
             100 * r["inj_risk"], r["exp_g"]))
