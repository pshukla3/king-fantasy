import pandas as pd

S = pd.read_csv("stat_projections_2026.csv",
                low_memory=False)
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def g(k):
    return float(V.get(k, 0.0))

PY, PT, PI = g("pass_yd"), g("pass_td"), g("pass_int")
RY, RT = g("rush_yd"), g("rush_td")
print("pass_yd %.3f (1 per %.0f) | pass_td %+.0f"
      % (PY, 1.0 / PY, PT))
print("pass_int %+.0f | rush_yd %.2f | rush_td %+.0f"
      % (PI, RY, RT))

Q = S[S["position"] == "QB"].copy()
print("\nQB rows in stat_projections: %d" % len(Q))
NEED = ["passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds", "attempts",
        "completions"]
for c in NEED:
    have = c in Q.columns
    print("  %-16s %s" % (c, "yes" if have else "MISSING"))

def col(c):
    if c in Q.columns:
        return pd.to_numeric(Q[c], errors="coerce").fillna(0)
    return pd.Series(0.0, index=Q.index)

Q["pyd"] = col("passing_yards")
Q["ptd"] = col("passing_tds")
Q["int"] = col("interceptions")
Q["ryd"] = col("rushing_yards")
Q["rtd"] = col("rushing_tds")
Q["att"] = col("attempts")

Q["p_pass"] = Q["pyd"] * PY + Q["ptd"] * PT
Q["p_int"] = Q["int"] * PI
Q["p_rush"] = Q["ryd"] * RY + Q["rtd"] * RT
Q["ppg"] = Q["p_pass"] + Q["p_int"] + Q["p_rush"]

B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "points", "exp_games", "depth_rank"]]
Q = Q.merge(B, on="player_id", how="left")
Q = Q.sort_values("ppg", ascending=False)

print("\n  %-22s %-4s %2s %5s %4s %4s %5s %4s"
      " %6s %6s %6s"
      % ("player", "tm", "dp", "pyd", "ptd", "int",
         "ryd", "rtd", "pass", "rush", "TOTAL"))
print("  " + "-" * 84)
n = 0
for _, r in Q.iterrows():
    if n >= 36:
        break
    n += 1
    dp = r["depth_rank"]
    dp = "%.0f" % dp if dp == dp else " "
    print("  %-22s %-4s %2s %5.0f %4.2f %4.2f %5.1f %4.2f"
          " %6.2f %6.2f %6.2f"
          % (str(r["player_display_name"])[:22],
             str(r["team"])[:4], dp,
             r["pyd"], r["ptd"], r["int"],
             r["ryd"], r["rtd"],
             r["p_pass"], r["p_rush"], r["ppg"]))

print("\n  rush share of total, top 12 rushers:")
Q["rsh"] = Q["p_rush"] / Q["ppg"].replace(0, float("nan"))
t = Q.nlargest(12, "p_rush")
for _, r in t.iterrows():
    print("    %-22s %5.2f of %5.2f  (%.0f%%)"
          % (str(r["player_display_name"])[:22],
             r["p_rush"], r["ppg"], 100 * r["rsh"]))
