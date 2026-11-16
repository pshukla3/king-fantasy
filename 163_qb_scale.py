import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
A = pd.read_csv("qb_all_2026.csv")[
    ["player_id", "start", "dr"]]
ROLE = {1: 0.86, 2: 0.26, 3: 0.16}
QB = B["position"] == "QB"
M = B[QB].merge(A, on="player_id", how="left")

fix = {}
derived = 0
for _, r in M.iterrows():
    dr = r["depth_rank"]
    dr = int(dr) if dr == dr else 3
    dr = min(max(dr, 1), 3)
    s = r["start"]
    if s != s:
        p = r["points"]
        if p != p or p <= 0:
            continue
        s = float(p) / ROLE[dr]
        derived += 1
    fix[r["player_id"]] = (float(s) if dr == 1
                           else float(s) * ROLE[dr])

print("QBs: %d | start from 147: %d | derived: %d"
      % (len(M), len(M) - derived, derived))
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
print("\nstarters %d | ranks %d to %d"
      % (len(st), int(st["qr"].min()),
         int(st["qr"].max())))
lows = st.nsmallest(4, "points")
print("\nlowest 4 starters:")
for _, r in lows.iterrows():
    print("  QB%-3d %-22s %-4s %6.2f"
          % (r["qr"], str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["points"]))
print("\nhighest 4 backups:")
for _, r in bk.nlargest(4, "points").iterrows():
    print("  QB%-3d %-22s dr%.0f %6.2f"
          % (r["qr"], str(r["player_display_name"])[:22],
             r["depth_rank"], r["points"]))
print("\ntop 10:")
for _, r in Q.head(10).iterrows():
    print("  QB%-3d %-22s %6.2f  x17 %4.0f"
          % (r["qr"], str(r["player_display_name"])[:22],
             r["points"], r["points"] * 17))
bad = bk[bk["qr"] < st["qr"].max()]
assert len(bad) == 0, "backup above a starter: %s" % (
    list(bad["player_display_name"].head(5)))
assert len(st) == 32, "expected 32 starters, got %d" % len(st)
a = Q[Q["player_display_name"].astype(str)
      .str.contains("Josh Allen", na=False)]
if len(a):
    v = float(a.iloc[0]["points"])
    print("\nAllen %.2f ppg (validated 22.90)" % v)
    assert v > 22.0, "Allen still discounted"
print("\nOK")
