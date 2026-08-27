import pandas as pd
import nflreadpy as nfl

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = "team" if "team" in H.columns else "recent_team"
PC = "fantasy_points_ppr"
print("history rows: %d | team col: %s" % (len(H), TC))

YRS = [int(y) for y in sorted(H["season"].unique()) if y <= 2025]
print("seasons: %d to %d" % (min(YRS), max(YRS)))

S = nfl.load_schedules(seasons=YRS)
S = S.to_pandas() if hasattr(S, "to_pandas") else S
if "game_type" in S.columns:
    S = S[S["game_type"] == "REG"]
S = S.dropna(subset=["home_score", "away_score"])
print("regular season games: %d" % len(S))

W = {}
for _, r in S.iterrows():
    sea = int(r["season"])
    h, a = r["home_team"], r["away_team"]
    W.setdefault((sea, h), 0.0)
    W.setdefault((sea, a), 0.0)
    if r["home_score"] > r["away_score"]:
        W[(sea, h)] += 1.0
    elif r["away_score"] > r["home_score"]:
        W[(sea, a)] += 1.0
    else:
        W[(sea, h)] += 0.5
        W[(sea, a)] += 0.5

WT = pd.DataFrame([{"season": k[0], "tm": k[1], "wins": v}
                   for k, v in W.items()])
WT.to_csv("team_wins_history.csv", index=False)
print("team-seasons: %d | mean wins %.2f"
      % (len(WT), WT["wins"].mean()))

H["opp_"] = H["carries"].fillna(0) + H["targets"].fillna(0)
H["tm_"] = H[TC]

rows = []
for (sea, tm), g in H.groupby(["season", "tm_"]):
    if sea > 2025:
        continue
    gm = g["week"].nunique()
    if gm < 8:
        continue
    for pos in ["QB", "RB", "WR", "TE"]:
        p = g[g["position"] == pos]
        if not len(p):
            continue
        a = p.groupby("player_id").agg(
            pts=(PC, "sum"), opp=("opp_", "sum")).reset_index()
        a = a.sort_values("opp", ascending=False).head(1)
        rows.append({"season": sea, "tm": tm, "pos": pos,
                     "ppg": float(a["pts"].sum()) / gm})

R = pd.DataFrame(rows).merge(WT, on=["season", "tm"], how="inner")
print("\npaired team-season-position rows: %d" % len(R))

print("\n=== MEASURED: team wins vs top-usage player ppg ===")
print("  pos      n       r    slope (ppg per win)")
print("  " + "-" * 42)
COEF = {}
for pos, g in R.groupby("pos"):
    rr = g["wins"].corr(g["ppg"])
    sl = g["ppg"].cov(g["wins"]) / g["wins"].var()
    COEF[pos] = {"r": rr, "slope": sl, "n": len(g)}
    print("  %-4s %5d  %+.3f    %+.3f" % (pos, len(g), rr, sl))
R.to_csv("wins_vs_ppg.csv", index=False)

V = pd.read_csv("win_totals_2026.csv")
LG = V["win_total"].mean()
print("\n2026 totals: %d teams | league mean %.2f" % (len(V), LG))

FIX = {"LAR": "LA", "ARZ": "ARI", "BLT": "BAL",
       "CLV": "CLE", "HST": "HOU"}
V["tm"] = V["team"].replace(FIX)

B = pd.read_csv("board_final.csv", low_memory=False)
B["tm"] = B["team"].replace(FIX)

MIN_R = 0.15
SKIP = ["QB"]  # reverse causation: good QBs cause wins,
               # so win total already encodes QB quality
use = {p: c for p, c in COEF.items()
       if abs(c["r"]) >= MIN_R and p not in SKIP}
drop = sorted([p for p in COEF if p not in use])
print("\nAPPLIED to: %s" % (sorted(use) or "NONE"))
if drop:
    print("DROPPED (|r| < %.2f, no reliable signal): %s"
          % (MIN_R, drop))

M = B.merge(V[["tm", "win_total"]], on="tm", how="left")
miss = sorted(set(M[M["win_total"].isna()]["tm"].dropna()))
if miss:
    print("NO WIN TOTAL MATCHED: %s" % miss)

def adj(r):
    c = use.get(r["position"])
    if c is None or r["win_total"] != r["win_total"]:
        return 0.0
    return c["slope"] * (r["win_total"] - LG)

M["gs_adj"] = M.apply(adj, axis=1)
M["points_gs"] = (M["points"] + M["gs_adj"]).clip(lower=0)
M.to_csv("board_gamescript.csv", index=False)

C = ["rank", "player_display_name", "position", "team",
     "win_total", "points", "gs_adj", "points_gs"]
print("\n=== BIGGEST PENALTIES ===")
print(M.nsmallest(12, "gs_adj")[C].round(2).to_string(index=False))
print("\n=== BIGGEST BOOSTS ===")
print(M.nlargest(12, "gs_adj")[C].round(2).to_string(index=False))
print("\nSaved board_gamescript.csv")
