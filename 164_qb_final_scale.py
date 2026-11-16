import os
import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
A = pd.read_csv("qb_all_2026.csv")
A = A[["player_id", "start"]].drop_duplicates("player_id")
ROLE = {1: 1.00, 2: 0.26, 3: 0.16, 4: 0.10}

md = B[B["player_display_name"].astype(str)
       .str.contains("Mendoza", na=False)]
print("=== MENDOZA STATE BEFORE ===")
if len(md):
    r = md.iloc[0]
    print("  points %.4f | depth_rank %s | team %s"
          % (r["points"], r["depth_rank"], r["team"]))
    print("  in qb_all_2026: %s"
          % (r["player_id"] in set(A["player_id"])))

MISS = "qb_missing_start.csv"
if not os.path.exists(MISS):
    RK = pd.read_csv("rookie_qb_seasons.csv")
    R5 = RK[RK["pick"] <= 5]
    SC = pd.read_csv("league_scoring.csv")
    V = dict(zip(SC["key"], SC["value"]))
    att = 30.3
    mp = (att * float(R5["ypa"].mean()) * float(V["pass_yd"])
          + att * float(R5["tdr"].mean()) * float(V["pass_td"])
          + att * 0.0211 * float(V["pass_int"])
          + float(R5["ryd"].sum() / R5["g"].sum())
          * float(V["rush_yd"])
          + float(R5["rtd"].sum() / R5["g"].sum())
          * float(V["rush_td"]))
    have = set(A["player_id"])
    rows = []
    for _, r in B[B["position"] == "QB"].iterrows():
        if r["player_id"] in have:
            continue
        nm = str(r["player_display_name"])
        rows.append({"player_id": r["player_id"],
                     "name": nm,
                     "start": mp if "Mendoza" in nm
                     else 12.0})
    pd.DataFrame(rows).to_csv(MISS, index=False)
    print("\nwrote %s (%d QBs, rookie start %.2f)"
          % (MISS, len(rows), mp))
MS = pd.read_csv(MISS)[["player_id", "start"]]
SRC = pd.concat([A, MS], ignore_index=True)
SRC = SRC.drop_duplicates("player_id")
print("start values available for %d QBs" % len(SRC))

M = B[B["position"] == "QB"][
    ["player_id", "depth_rank"]].merge(
    SRC, on="player_id", how="left")
fix = {}
for _, r in M.iterrows():
    s = r["start"]
    if s != s:
        continue
    dr = r["depth_rank"]
    dr = int(dr) if dr == dr else 3
    dr = min(max(dr, 1), 4)
    fix[r["player_id"]] = float(s) * ROLE[dr]

B["points"] = B.apply(
    lambda r: fix.get(r["player_id"], r["points"])
    if r["position"] == "QB" else r["points"], axis=1)
B.to_csv("board_final.csv", index=False)

Q = B[B["position"] == "QB"].copy()
Q = Q[Q["points"].notna() & (Q["points"] > 0)]
Q = Q.sort_values("points", ascending=False)
Q = Q.reset_index(drop=True)
Q["qr"] = Q.index + 1
st = Q[Q["depth_rank"] == 1]
bk = Q[Q["depth_rank"] >= 2]
print("\nstarters %d | worst starter rank %d"
      % (len(st), int(st["qr"].max())))
print("\nbottom 5 starters:")
for _, r in st.nsmallest(5, "points").iterrows():
    print("  QB%-3d %-22s %-4s %6.2f"
          % (r["qr"], str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["points"]))
print("\ntop 3 backups:")
for _, r in bk.nlargest(3, "points").iterrows():
    print("  QB%-3d %-22s dr%.0f %6.2f"
          % (r["qr"], str(r["player_display_name"])[:22],
             r["depth_rank"], r["points"]))
bad = bk[bk["qr"] < st["qr"].max()]
assert len(bad) == 0, "backup above starter: %s" % list(
    bad["player_display_name"].head(5))
assert len(st) == 32, "expected 32 starters got %d" % len(st)
al = Q[Q["player_display_name"].astype(str)
       .str.contains("Josh Allen", na=False)]
assert float(al.iloc[0]["points"]) > 22.0, "Allen low"
print("\nAllen %.2f | Mendoza %.2f"
      % (float(al.iloc[0]["points"]),
         float(Q[Q["player_display_name"].astype(str)
                 .str.contains("Mendoza", na=False)]
               .iloc[0]["points"])))
print("OK - idempotent, safe to re-run")
