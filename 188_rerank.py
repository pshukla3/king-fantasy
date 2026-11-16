import pandas as pd
import numpy as np

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
st = B["status"].astype(str).str.upper().fillna("")
gm = pd.to_numeric(B.get("games_mult"),
                   errors="coerce").fillna(1.0)

print("=== STATUS VALUES ON THE BOARD ===")
vc = B["status"].astype(str).value_counts()
for k, v in vc.head(12).items():
    print("  %-28s %d" % (k[:28], v))

OUT = ["OUT", "IR", "INJURED RESERVE", "PUP", "NFI",
       "SUSPEND", "RETIRE", "SEASON", "DOUBTFUL"]
mask = st.apply(lambda s: any(w in s for w in OUT))
mask = mask | (gm <= 0.05)

print("\n=== ZEROED OUT ===")
z = B[mask]
if not len(z):
    print("  none matched")
for _, r in z.sort_values("pp", ascending=False).head(20).iterrows():
    print("  %-24s %-4s %-4s was %6.2f ppg  [%s]"
          % (str(r["player_display_name"])[:24],
             str(r["position"])[:4], str(r["team"])[:4],
             0.0 if r["pp"] != r["pp"] else r["pp"],
             str(r["status"])[:20]))
print("  total zeroed: %d" % int(mask.sum()))

B.loc[mask, "points"] = 0.0
B["pp"] = pd.to_numeric(B["points"], errors="coerce").fillna(0.0)

REPL = {"QB": 10, "RB": 30, "WR": 40, "TE": 12,
        "K": 10, "DST": 10, "DEF": 10}
B["vorp"] = 0.0
for pos, n in REPL.items():
    m = B["position"].astype(str) == pos
    d = B.loc[m, "pp"].sort_values(ascending=False)
    if len(d) < n:
        continue
    base = float(d.iloc[n - 1])
    B.loc[m, "vorp"] = B.loc[m, "pp"] - base
    print("  %-4s replacement = %.2f ppg (n=%d)"
          % (pos, base, int(m.sum())))

B = B.sort_values(["pp", "vorp"],
                  ascending=[False, False]).reset_index(drop=True)
B["rank"] = B.index + 1
B["pos_rank"] = B.groupby("position").cumcount() + 1
eg = pd.to_numeric(B["exp_games"], errors="coerce").fillna(17.0)
B["season_pts"] = (B["pp"] * 17.0).round(1)
B["value"] = (B["vorp"] * eg).round(2)
B.to_csv("board_final.csv", index=False)

print("\n=== ORDERING CHECK ===")
bad = int((B["pp"].diff().dropna() > 1e-9).sum())
print("  rows where a lower rank has MORE ppg: %d" % bad)
assert bad == 0, "ranking is not monotonic in ppg"

print("\n=== TOP 20 OVERALL ===")
print("  %-3s %-24s %-4s %-4s %7s %7s"
      % ("#", "player", "pos", "tm", "ppg", "x17"))
for _, r in B.head(20).iterrows():
    print("  %-3d %-24s %-4s %-4s %7.2f %7.0f"
          % (r["rank"], str(r["player_display_name"])[:24],
             str(r["position"])[:4], str(r["team"])[:4],
             r["pp"], r["pp"] * 17))

print("\n=== BOTTOM: ZEROED PLAYERS SIT LAST ===")
print("  players at 0.00 ppg: %d" % int((B["pp"] == 0).sum()))
print("  lowest non-zero rank: %d"
      % int(B[B["pp"] > 0]["rank"].max()))
