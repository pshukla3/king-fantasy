import numpy as np
import nflreadpy as nfl

YR = [2024, 2025, 2026]
d = nfl.load_player_stats(YR).to_pandas()
for c in ("targets", "receptions", "receiving_yards"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)

sn = nfl.load_snap_counts(YR).to_pandas()
sn = sn[["season", "week", "player", "team",
         "offense_pct", "offense_snaps"]]
sn["offense_pct"] = sn["offense_pct"].fillna(0.0).astype(float)
# some feeds store 0-100 instead of 0-1
if sn["offense_pct"].max() > 1.5:
    sn["offense_pct"] = sn["offense_pct"] / 100.0

m = d.merge(sn, left_on=["season", "week",
                         "player_display_name", "team"],
            right_on=["season", "week", "player", "team"],
            how="left")
print("rows matched to snap data: %.0f%%"
      % (m["offense_pct"].notna().mean() * 100))

for nm in ("Justin Jefferson", "Jaxon Smith-Njigba",
           "Malik Nabers"):
    g = m[m["player_display_name"] == nm].sort_values(
        ["season", "week"]).tail(10)
    if not len(g):
        continue
    base = g["offense_pct"].median()
    print("\n=== %s  (median snap%% %.0f%%) ===" % (nm, base * 100))
    print("  %-6s %-4s %7s %6s %6s %7s  %s"
          % ("SEA", "WK", "SNAP%", "TGT", "REC", "YDS", ""))
    for _, r in g.iterrows():
        p = r["offense_pct"]
        flag = ""
        if p == p and base > 0 and p < base * 0.6:
            flag = "  <-- PARTIAL GAME"
        print("  %-6d %-4d %6.0f%% %6.0f %6.0f %7.0f%s"
              % (r["season"], r["week"],
                 (p if p == p else 0) * 100,
                 r["targets"], r["receptions"],
                 r["receiving_yards"], flag))

print("\n=== how much do partial games distort a rate? ===")
w = m[m["position"].isin(["WR", "TE"])
      & m["offense_pct"].notna()].copy()
med = w.groupby("player_id")["offense_pct"].transform("median")
w["part"] = w["offense_pct"] < med * 0.6
a, b = w[~w["part"]], w[w["part"]]
print("  full games   : %5.1f tgt  %5.1f yds  (n=%d)"
      % (a["targets"].mean(), a["receiving_yards"].mean(),
         len(a)))
print("  partial games: %5.1f tgt  %5.1f yds  (n=%d)"
      % (b["targets"].mean(), b["receiving_yards"].mean(),
         len(b)))
print("  -> a partial game understates a player by %.0f%%"
      % ((1 - b["receiving_yards"].mean()
          / max(1e-9, a["receiving_yards"].mean())) * 100))
