import pandas as pd
import nflreadpy as nfl

YRS = [2023, 2024, 2025]
print("pulling pbp for %s ..." % YRS)
P = nfl.load_pbp(seasons=YRS)
P = P.to_pandas() if hasattr(P, "to_pandas") else P
print("pbp rows: %d" % len(P))

D = P[P["defteam"].notna()].copy()
for c in ["sack", "interception", "fumble_lost", "safety",
          "touchdown"]:
    D[c] = pd.to_numeric(D.get(c), errors="coerce").fillna(0)

D["dtd"] = ((D["touchdown"] == 1)
            & (D.get("td_team") == D["defteam"])).astype(int)

G = D.groupby(["season", "week", "defteam"]).agg(
    sack=("sack", "sum"),
    intc=("interception", "sum"),
    fum=("fumble_lost", "sum"),
    saf=("safety", "sum"),
    dtd=("dtd", "sum")).reset_index()
print("team-games: %d" % len(G))

S = nfl.load_schedules(seasons=YRS)
S = S.to_pandas() if hasattr(S, "to_pandas") else S
if "game_type" in S.columns:
    S = S[S["game_type"] == "REG"]
S = S.dropna(subset=["home_score", "away_score"])

rows = []
for _, r in S.iterrows():
    rows.append({"season": int(r["season"]), "week": int(r["week"]),
                 "defteam": r["home_team"], "pa": r["away_score"]})
    rows.append({"season": int(r["season"]), "week": int(r["week"]),
                 "defteam": r["away_team"], "pa": r["home_score"]})
PA = pd.DataFrame(rows)
G = G.merge(PA, on=["season", "week", "defteam"], how="inner")
print("after merging points allowed: %d" % len(G))

def pa_pts(x):
    if x == 0:
        return 10.0
    if x <= 6:
        return 7.0
    if x <= 13:
        return 4.0
    if x <= 17:
        return 1.0
    if x <= 27:
        return 0.0
    if x <= 34:
        return -1.0
    if x <= 45:
        return -3.0
    return -5.0

G["pa_pts"] = G["pa"].apply(pa_pts)
G["dst_pts"] = (G["sack"] * 1.0 + G["intc"] * 2.0
                + G["fum"] * 2.0 + G["saf"] * 2.0
                + G["dtd"] * 6.0 + G["pa_pts"])
G.to_csv("dst_weekly.csv", index=False)

print("\n=== LEAGUE-WIDE DST SCORING ===")
print("  mean %.2f | median %.2f | sd %.2f"
      % (G["dst_pts"].mean(), G["dst_pts"].median(),
         G["dst_pts"].std()))
print("  10th pct %.1f | 90th pct %.1f"
      % (G["dst_pts"].quantile(0.10),
         G["dst_pts"].quantile(0.90)))

T = G.groupby(["season", "defteam"])["dst_pts"].mean().reset_index()
nx = T.copy()
nx["season"] = nx["season"] - 1
nx = nx.rename(columns={"dst_pts": "next"})
PR = T.merge(nx, on=["season", "defteam"], how="inner")
r = PR["dst_pts"].corr(PR["next"])
print("\n=== IS DST SCORING REPEATABLE? ===")
print("  n = %d team-season pairs" % len(PR))
print("  year N vs N+1 correlation: r = %.3f" % r)
print("  compare: WR %.3f | RB %.3f | QB %.3f"
      % (0.765, 0.709, 0.56))

L = T[T["season"] == 2025].sort_values(
    "dst_pts", ascending=False).reset_index(drop=True)
L["rank"] = L.index + 1
L.to_csv("dst_projections_2026.csv", index=False)
print("\n=== 2025 DST PPG, ALL 32 ===")
print(L[["rank", "defteam", "dst_pts"]].round(2).to_string(
    index=False))

sea = L[L["defteam"] == "SEA"]
if len(sea):
    v = float(sea["dst_pts"].iloc[0])
    print("\n  SEATTLE measured: %.2f ppg (was 7.00 INVENTED)"
          % v)
    print("  delta to the fabricated number: %+.2f" % (v - 7.0))
print("\nSaved dst_weekly.csv and dst_projections_2026.csv")
