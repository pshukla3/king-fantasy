import pandas as pd

G = pd.read_csv("dst_weekly_v2.csv")
LG = G["dst_pts"].mean()
R = 0.282

T = G.groupby(["season", "defteam"])["dst_pts"].mean().reset_index()
L = T[T["season"] == 2025].copy()
L["proj_2026"] = LG + R * (L["dst_pts"] - LG)
L = L.sort_values("proj_2026", ascending=False).reset_index(drop=True)
L["rank"] = L.index + 1
L["basis"] = "Sleeper scoring, 2017-2025, r=%.3f" % R
L.to_csv("dst_projections_2026.csv", index=False)

print("league mean %.2f | regression factor %.3f" % (LG, R))
print("\n=== 2026 DST PROJECTIONS (Sleeper scoring) ===")
print(L[["rank", "defteam", "dst_pts", "proj_2026"]].round(2)
      .to_string(index=False))
print("\nraw 2025 spread  %.2f to %.2f  (%.2f gap)"
      % (L["dst_pts"].min(), L["dst_pts"].max(),
         L["dst_pts"].max() - L["dst_pts"].min()))
print("projected spread %.2f to %.2f  (%.2f gap)"
      % (L["proj_2026"].min(), L["proj_2026"].max(),
         L["proj_2026"].max() - L["proj_2026"].min()))

s = L[L["defteam"] == "SEA"]
if len(s):
    print("\nSEATTLE (yours): %.2f raw -> %.2f projected"
          % (s["dst_pts"].iloc[0], s["proj_2026"].iloc[0]))
    print("  the 7.00 in your roster file is still invented")
