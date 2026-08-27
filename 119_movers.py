import pandas as pd
import nflreadpy as nfl

R = nfl.load_rosters(seasons=[2026])
R = R.to_pandas() if hasattr(R, "to_pandas") else R
R.to_csv("rosters_2026.csv", index=False)
print("roster rows: %d" % len(R))

D = nfl.load_depth_charts(seasons=[2026])
D = D.to_pandas() if hasattr(D, "to_pandas") else D
D["_mx"] = D.groupby("team")["dt"].transform("max")
D = D[D["dt"] == D["_mx"]].copy()
D["pos_rank"] = pd.to_numeric(D["pos_rank"], errors="coerce")
D["pos_abb"] = D["pos_abb"].astype(str).str.upper()
D.to_csv("depth_latest.csv", index=False)
print("depth snapshot: %s" % str(D["dt"].max())[:10])
print("depth rows: %d | teams: %d"
      % (len(D), D["team"].nunique()))

CUR = R[["gsis_id", "team", "position"]].dropna(
    subset=["gsis_id"]).drop_duplicates("gsis_id")
CUR = CUR.rename(columns={"gsis_id": "player_id",
                          "team": "cur_tm"})
print("players with a 2026 team: %d" % len(CUR))

B = pd.read_csv("board_final.csv", low_memory=False)
B = B.merge(CUR[["player_id", "cur_tm"]],
            on="player_id", how="left")
SK = ["QB", "RB", "WR", "TE"]
m = B[B["position"].isin(SK)].copy()
bad = m[m["cur_tm"].notna()
        & (m["team"].astype(str) != m["cur_tm"])]
print("\n=== BOARD TEAM MISMATCHES ===")
print("skill players on board: %d" % len(m))
print("wrong team: %d" % len(bad))
C = ["rank", "player_display_name", "position",
     "team", "cur_tm", "points"]
print(bad.nsmallest(30, "rank")[C].to_string(index=False))

print("\n=== SPOT CHECK ===")
for nm in ["Deebo Samuel", "Jauan Jennings",
           "Mike Evans", "A.J. Brown", "DJ Moore"]:
    h = B[B["player_display_name"].astype(str)
          .str.contains(nm, na=False)]
    if not len(h):
        print("  %-20s NOT ON BOARD" % nm)
        continue
    r = h.iloc[0]
    print("  %-20s board %-4s roster %-4s"
          % (nm, r["team"], r["cur_tm"]))

OFF = ["QB", "RB", "WR", "TE"]
DR = D[D["pos_abb"].isin(OFF)].copy()
DR = DR.sort_values("pos_rank").groupby(
    "gsis_id").head(1)[["gsis_id", "team",
                        "pos_abb", "pos_rank"]]
DR = DR.rename(columns={"gsis_id": "player_id",
                        "pos_rank": "depth_rank"})
B = B.merge(DR[["player_id", "depth_rank"]],
            on="player_id", how="left")

fixed = int((B["cur_tm"].notna()
             & (B["team"].astype(str)
                != B["cur_tm"])).sum())
B["team"] = B["cur_tm"].fillna(B["team"])
B = B.drop(columns=["cur_tm"])
B.to_csv("board_final.csv", index=False)
print("\nteams corrected on board: %d" % fixed)

dr = B[B["position"].isin(OFF)]["depth_rank"]
print("depth rank filled: %d of %d skill players"
      % (int(dr.notna().sum()), len(dr)))
print("\n=== 2026 STARTERS BY DEPTH RANK ===")
for p in OFF:
    x = B[(B["position"] == p)
          & (B["depth_rank"] == 1)]
    print("  %-3s %d listed as their team's #1"
          % (p, len(x)))
