import json, re
import numpy as np
import nflreadpy as nfl

d = nfl.load_player_stats([2025, 2026]).to_pandas()
for c in ("attempts", "targets", "receiving_yards",
          "receptions"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)

# who started at QB for each team each week
q = d[(d["position"] == "QB") & (d["attempts"] >= 10)]
ST = {}
for (s, w, t), g in q.groupby(["season", "week", "team"]):
    ST[(s, w, t)] = g.sort_values(
        "attempts", ascending=False)["player_display_name"].iloc[0]

# that team's most common starter = QB1
from collections import Counter, defaultdict
cnt = defaultdict(Counter)
for (s, w, t), nm in ST.items():
    if s == 2026:
        cnt[t][nm] += 1
QB1 = {t: c.most_common(1)[0][0] for t, c in cnt.items()}

print("=== JA'MARR CHASE game log ===")
c = d[d["player_display_name"] == "Ja'Marr Chase"].copy()
c = c.sort_values(["season", "week"])
print("  %-6s %-4s %-20s %6s %6s %6s %s"
      % ("SEA", "WK", "QB", "TGT", "REC", "YDS", ""))
for _, r in c.tail(14).iterrows():
    qb = ST.get((r["season"], r["week"], r["team"]), "?")
    flag = "" if qb == QB1.get(r["team"]) else "  <-- BACKUP QB"
    print("  %-6d %-4d %-20s %6.0f %6.0f %6.0f%s"
          % (r["season"], r["week"], qb[:20], r["targets"],
             r["receptions"], r["receiving_yards"], flag))

print("\n=== does QB1 vs backup move pass-catchers? ===")
r = d[d["position"].isin(["WR", "TE"]) & (d["targets"] >= 2)].copy()
r["qb"] = [ST.get((s, w, t)) for s, w, t
           in zip(r["season"], r["week"], r["team"])]
r["is1"] = [q == QB1.get(t) for q, t in zip(r["qb"], r["team"])]
r["ypt"] = r["receiving_yards"] / r["targets"]
r["cr"] = r["receptions"] / r["targets"]
a, b = r[r["is1"]], r[~r["is1"]]
print("  %-14s %8s %8s %8s"
      % ("", "YDS/GM", "YDS/TGT", "CATCH%"))
print("  %-14s %8.1f %8.2f %7.1f%%  (n=%d)"
      % ("QB1 starts", a["receiving_yards"].mean(),
         a["ypt"].mean(), a["cr"].mean() * 100, len(a)))
print("  %-14s %8.1f %8.2f %7.1f%%  (n=%d)"
      % ("backup QB", b["receiving_yards"].mean(),
         b["ypt"].mean(), b["cr"].mean() * 100, len(b)))
if len(b) > 30:
    m = a["receiving_yards"].mean() / max(1e-9,
        b["receiving_yards"].mean())
    print("  -> pass-catchers gain %.0f%% with QB1 starting"
          % ((m - 1) * 100))
    json.dump({"qb1_mult": round(float(m), 4)},
              open("qbquality.json", "w"))
    print("  wrote qbquality.json")
