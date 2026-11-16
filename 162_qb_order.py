import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
A = pd.read_csv("qb_all_2026.csv")
A = A[["player_id", "start", "exp", "dr"]]
QB = B["position"] == "QB"
print("QBs on board: %d" % int(QB.sum()))

M = B[QB].merge(A, on="player_id", how="left")
miss = M[M["exp"].isna()]
print("QBs NOT covered by 147: %d" % len(miss))
for _, r in miss.iterrows():
    dr = r["depth_rank"]
    dr = dr if dr == dr else 3
    print("  %-24s dr%.0f  board %.2f"
          % (str(r["player_display_name"])[:24], dr,
             r["points"] if r["points"] == r["points"]
             else 0))

ROLE = {1: 0.86, 2: 0.26, 3: 0.16}
fix = {}
for _, r in M.iterrows():
    pid = r["player_id"]
    if r["exp"] == r["exp"]:
        fix[pid] = float(r["exp"])
        continue
    p = r["points"]
    if p != p or p <= 0:
        continue
    dr = r["depth_rank"]
    dr = int(dr) if dr == dr else 3
    dr = min(max(dr, 1), 3)
    fix[pid] = float(p) * ROLE[dr] / ROLE[1]

B["points"] = B.apply(
    lambda r: fix.get(r["player_id"], r["points"])
    if r["position"] == "QB" else r["points"], axis=1)
B.to_csv("board_final.csv", index=False)

Q = B[B["position"] == "QB"].copy()
Q = Q[Q["points"].notna()].sort_values(
    "points", ascending=False).reset_index(drop=True)
Q["qr"] = Q.index + 1
st = Q[Q["depth_rank"] == 1]
bk = Q[Q["depth_rank"] >= 2]
worst = int(st["qr"].max())
bad = bk[bk["qr"] < worst]
print("\nstarters %d | worst starter rank %d"
      % (len(st), worst))
if len(bad):
    print("STILL OUT OF ORDER:")
    for _, r in bad.iterrows():
        print("  QB%-3d %-22s dr%.0f %.2f"
              % (r["qr"], str(r["player_display_name"])[:22],
                 r["depth_rank"], r["points"]))
else:
    print("clean: all %d starters rank above every backup"
          % len(st))
print("\ntop 12 QBs on board:")
for _, r in Q.head(12).iterrows():
    print("  QB%-3d %-22s dr%.0f %6.2f"
          % (r["qr"], str(r["player_display_name"])[:22],
             r["depth_rank"], r["points"]))
assert len(bad) == 0, "backup QB outranks a starter"
assert len(st) == 32, "expected 32 starting QBs"
print("\nOK")
