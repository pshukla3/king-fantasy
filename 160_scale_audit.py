import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
B["position"] = B["position"].replace({"DST": "DEF"})
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

print("=== WHERE exp_games STILL BITES ===")
Q = B[B["points"].notna() & (B["points"] > 0)].copy()
Q["eg"] = pd.to_numeric(Q["exp_games"], errors="coerce")
Q["mult"] = (Q["eg"] / 17.0).clip(upper=1.0)
Q["shown"] = Q["points"] * Q["mult"]
Q["loss"] = 100.0 * (Q["shown"] / Q["points"] - 1)
for p in ["QB", "RB", "WR", "TE", "K", "DEF"]:
    d = Q[Q["position"] == p]
    if not len(d):
        continue
    print("  %-4s n=%3d  mean exp_games %5.1f"
          "  mean shown-vs-proj %+6.1f%%"
          % (p, len(d), d["eg"].mean(), d["loss"].mean()))

print("\n=== OUR BOARD IN SEASON PPR POINTS (x17) ===")
print("  ESPN anchor: Davante Adams 235.6 pts / 13.86 ppg")
print("  (124 tgt, 68 rec, 1016 yd, 11 TD)\n")
for p in ["RB", "WR", "TE"]:
    d = Q[Q["position"] == p].nlargest(12, "points")
    print("  --- %s ---" % p)
    print("  %-24s %6s %7s %7s"
          % ("player", "ppg", "x17", "shown17"))
    for _, r in d.iterrows():
        print("  %-24s %6.2f %7.0f %7.0f"
              % (str(r["player_display_name"])[:24],
                 r["points"], r["points"] * 17,
                 r["shown"] * 17))
    print("")

a = Q[Q["player_display_name"].astype(str)
      .str.contains("Davante Adams", na=False)]
print("=== DIRECT COMPARISON ===")
if len(a):
    r = a.iloc[0]
    print("  Davante Adams")
    print("    ESPN     13.86 ppg   236 pts")
    print("    our proj %5.2f ppg  %4.0f pts  (%+.0f%%)"
          % (r["points"], r["points"] * 17,
             100 * (r["points"] / 13.86 - 1)))
    print("    displayed %4.2f ppg  %4.0f pts  (%+.0f%%)"
          % (r["shown"], r["shown"] * 17,
             100 * (r["shown"] / 13.86 - 1)))
else:
    print("  Adams NOT ON BOARD")

print("\n=== QB ORDER CHECK ===")
QB = B[B["position"] == "QB"].copy()
QB = QB[QB["points"].notna()].sort_values(
    "points", ascending=False).reset_index(drop=True)
QB["qrank"] = QB.index + 1
st = QB[QB["depth_rank"] == 1]
bk = QB[QB["depth_rank"] >= 2]
print("  starters: %d | worst starter rank %d"
      % (len(st), int(st["qrank"].max())))
print("  backups above the worst starter:")
bad = bk[bk["qrank"] < st["qrank"].max()]
if len(bad):
    for _, r in bad.head(12).iterrows():
        print("    QB%-3d %-22s dr%.0f  %.2f"
              % (r["qrank"],
                 str(r["player_display_name"])[:22],
                 r["depth_rank"], r["points"]))
else:
    print("    none - ordering is clean")
