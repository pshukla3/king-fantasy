import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
QB = B["position"] == "QB"

print("=== DUPLICATE player_id CHECK ===")
d = B.loc[QB, "player_id"]
dups = d[d.duplicated(keep=False)]
print("  QB rows %d | unique ids %d | dup rows %d"
      % (int(QB.sum()), d.nunique(), len(dups)))
if len(dups):
    sh = B[QB & B["player_id"].isin(dups)]
    print(sh[["player_id", "player_display_name",
              "depth_rank", "points"]]
          .sort_values("player_id").head(12)
          .to_string(index=False))

A = pd.read_csv("qb_all_2026.csv")[["player_id", "start"]]
MS = pd.read_csv("qb_missing_start.csv")[
    ["player_id", "start"]]
SRC = pd.concat([A, MS], ignore_index=True)
SRC = SRC.drop_duplicates("player_id")
S = SRC.set_index("player_id")["start"]
print("\nstart values: %d" % len(S))

ROLE = {1: 1.00, 2: 0.26, 3: 0.16, 4: 0.10}
st = B.loc[QB, "player_id"].map(S)
dr = (pd.to_numeric(B.loc[QB, "depth_rank"],
                    errors="coerce")
      .fillna(3).clip(1, 4).round().astype(int))
new = st * dr.map(ROLE)
B.loc[QB, "points"] = new.fillna(B.loc[QB, "points"])
B.to_csv("board_final.csv", index=False)

Q = B[QB].copy()
Q = Q[Q["points"].notna() & (Q["points"] > 0)]
Q = Q.sort_values("points", ascending=False)
Q = Q.reset_index(drop=True)
Q["qr"] = Q.index + 1
sta = Q[Q["depth_rank"] == 1]
bk = Q[Q["depth_rank"] >= 2]
print("\nstarters %d | ranks %d to %d"
      % (len(sta), int(sta["qr"].min()),
         int(sta["qr"].max())))
print("\nbottom 5 starters:")
for _, r in sta.nsmallest(5, "points").iterrows():
    print("  QB%-3d %-22s %-4s %6.2f  x17 %4.0f"
          % (r["qr"], str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["points"],
             r["points"] * 17))
print("\ntop 3 backups:")
for _, r in bk.nlargest(3, "points").iterrows():
    print("  QB%-3d %-22s dr%.0f %6.2f"
          % (r["qr"], str(r["player_display_name"])[:22],
             r["depth_rank"], r["points"]))
bad = bk[bk["qr"] < sta["qr"].max()]
assert len(bad) == 0, "backup above starter: %s" % list(
    bad["player_display_name"].head(5))
assert len(sta) == 32, "expected 32 starters got %d" % len(sta)
al = float(Q[Q["player_display_name"].astype(str)
             .str.contains("Josh Allen", na=False)]
           .iloc[0]["points"])
me = float(Q[Q["player_display_name"].astype(str)
             .str.contains("Mendoza", na=False)]
           .iloc[0]["points"])
assert al > 22.0, "Allen low: %.2f" % al
assert me > 12.0, "Mendoza low: %.2f" % me
print("\nAllen %.2f | Mendoza %.2f" % (al, me))
print("OK")
