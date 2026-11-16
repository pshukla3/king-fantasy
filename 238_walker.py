import json
import pandas as pd
import numpy as np

NAME = "Kenneth Walker"
B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
h = B[B["player_display_name"].astype(str)
      .str.contains(NAME, na=False)]
if not len(h):
    raise SystemExit("not on board")
r = h.iloc[0]
TM = str(r["team"])
print("=== BOARD ROW ===")
print("  %s | %s | ovr #%d | %s%d | %.2f ppg | src %s"
      % (r["player_display_name"], TM, int(r["rank"]),
         r["position"], int(r["pos_rank"]), r["pp"],
         str(r.get("src"))))

print("\n=== %s RB ROOM, OUR BOARD ===" % TM)
d = B[(B["team"] == TM) & (B["position"] == "RB")
      & (B["pp"] > 0)].sort_values("pp",
                                   ascending=False)
for _, x in d.head(6).iterrows():
    print("  %-24s %6.2f ppg  ovr #%d"
          % (str(x["player_display_name"])[:24],
             x["pp"], int(x["rank"])))

try:
    PJ = json.load(open("sleeper_players_fresh.json"))
except IOError:
    PJ = {}
print("\n=== LIVE SLEEPER DEPTH CHART, %s RB ===" % TM)
rows = [(d2.get("depth_chart_order") or 99,
         d2.get("full_name"))
        for d2 in PJ.values()
        if d2.get("team") == TM
        and d2.get("position") == "RB"]
for o, nm in sorted(rows)[:6]:
    print("  %-3s %s" % ("--" if o == 99 else o, nm))

S = pd.read_csv("pos_season_panel.csv",
                low_memory=False)
q = S[(S["season"] == 2025)
      & (S["player_id"] == r["player_id"])]
print("\n=== HIS 2025 USAGE (old team) ===")
if len(q):
    x = q.iloc[0]
    print("  %s | %.1f car/g | car_share %.3f"
          % (x["team"], x["cpg"], x["car_share"]))
    print("  opp_share %.3f | %.2f ppg | %.0f games"
          % (x["opp_share"], x["ppg"], x["g"]))
else:
    print("  no 2025 panel row")

print("\n" + "=" * 58)
print("=== WHAT DOES A TEAM'S LEAD RB GET? ===")
A = S[(S["position"] == "RB") & (S["g"] >= 10)].copy()
for c in ["opp_share", "car_share", "ppg"]:
    A[c] = pd.to_numeric(A[c], errors="coerce")
A = A.dropna(subset=["opp_share", "car_share", "ppg"])
lead = A.loc[A.groupby(["team", "season"])
             ["car_share"].idxmax()]
print("  team-seasons with a lead RB: %d" % len(lead))
for qn in [25, 50, 75, 90]:
    print("    p%-3d opp_share %.3f"
          % (qn, lead["opp_share"].quantile(qn / 100.0)))
print("  mean %.3f | sd %.3f"
      % (lead["opp_share"].mean(),
         lead["opp_share"].std()))

x = A["opp_share"].values
y = A["ppg"].values
dx = x - x.mean()
b1 = float((dx * (y - y.mean())).sum() / (dx ** 2).sum())
b0 = float(y.mean() - b1 * x.mean())
mae = float(np.abs(b0 + b1 * x - y).mean())
print("\n  ppg = %.2f + %.2f x opp_share" % (b0, b1))
print("  fit on %d RB seasons | MAE %.2f ppg"
      % (len(A), mae))
print("  0.30 -> %.2f | 0.45 -> %.2f | 0.55 -> %.2f ppg"
      % (b0 + b1 * .30, b0 + b1 * .45, b0 + b1 * .55))

print("\n" + "=" * 58)
print("=== REBUILDING THE %s BACKFIELD ===" % TM)
LEAD = float(lead["opp_share"].median())
A25 = A[A["season"] == 2025]
room = B[(B["team"] == TM) & (B["position"] == "RB")
         & (B["pp"] > 0)].sort_values(
    "pp", ascending=False).copy()
cur = {}
for _, xx in room.iterrows():
    z = A25[A25["player_id"] == xx["player_id"]]
    cur[xx["player_id"]] = (float(z.iloc[0]["opp_share"])
                            if len(z) else 0.08)
me = r["player_id"]
rest = [k for k in cur if k != me]
tot = sum(cur[k] for k in rest) or 1.0
new = {me: LEAD}
for k in rest:
    new[k] = max(0.0, 1.0 - LEAD) * cur[k] / tot

print("  lead share used %.3f (league median)" % LEAD)
print("\n  %-22s %7s %7s %7s %7s"
      % ("player", "shr in", "shr out", "old", "NEW"))
print("  " + "-" * 56)
OUT = []
for _, xx in room.iterrows():
    k = xx["player_id"]
    v = max(0.0, b0 + b1 * new[k])
    OUT.append({"player_id": k,
                "player_display_name":
                    xx["player_display_name"],
                "new_ppg": round(v, 2),
                "reason": "%s backfield reset" % TM})
    print("  %-22s %7.3f %7.3f %7.2f %7.2f"
          % (str(xx["player_display_name"])[:22],
             cur[k], new[k], xx["pp"], v))
pd.DataFrame(OUT).to_csv("situation_overrides.csv",
                         index=False)
print("\n  wrote situation_overrides.csv - NOT applied")
print("  MEASURED: lead-RB share, ppg-per-share fit")
print("  ASSUMED: that he holds the lead job all year")
