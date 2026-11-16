import pandas as pd
import numpy as np

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
Q = H[H["position"] == "QB"].copy()
for c in ["attempts", "passing_tds"]:
    Q[c] = pd.to_numeric(Q[c], errors="coerce").fillna(0)

S = Q.groupby(["player_id", "season"]).agg(
    att=("attempts", "sum"),
    td=("passing_tds", "sum")).reset_index()
S = S[S["att"] >= 100].copy()
S["tdr"] = S["td"] / S["att"]
LG = S["td"].sum() / S["att"].sum()

N = S[["player_id", "season", "tdr", "att"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"tdr": "tdr_n", "att": "att_n"})
P = S.merge(N, on=["player_id", "season"], how="inner")

yrs = sorted(P["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = P[P["season"] < cut]
TS = P[P["season"] >= cut]

print("league pass TD rate %.4f | pairs %d" % (LG, len(P)))
print("\n=== k BY MEAN ABSOLUTE ERROR (correct test) ===")
print("     k   train MAE   test MAE")
best = (0, 9.9)
for k in [0, 50, 100, 200, 300, 400, 600, 900, 1400]:
    f = lambda d: (d["td"] + k * LG) / (d["att"] + k)
    e0 = (f(TR) - TR["tdr_n"]).abs().mean()
    e1 = (f(TS) - TS["tdr_n"]).abs().mean()
    print("  %5d    %.5f    %.5f" % (k, e0, e1))
    if e0 < best[1]:
        best = (k, e0)
K = best[0]
print("\n  best k on train = %d attempts" % K)
print("  a QB with %d career attempts gets 50%% shrink" % K)

CAR = S.groupby("player_id").agg(
    catt=("att", "sum"), ctd=("td", "sum")).reset_index()

SP = pd.read_csv("stat_projections_2026.csv",
                 low_memory=False)
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
PY, PT = float(V["pass_yd"]), float(V["pass_td"])
RY, RT = float(V["rush_yd"]), float(V["rush_td"])
PI = float(V["pass_int"])

X = SP[SP["position"] == "QB"].copy()
for c in ["attempts", "passing_yards", "passing_tds",
          "rushing_yards", "rushing_tds"]:
    X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
X = X.merge(CAR, on="player_id", how="left")
X["catt"] = X["catt"].fillna(0)

X["tdr_p"] = np.where(X["attempts"] > 0,
                      X["passing_tds"] / X["attempts"], LG)
X["tdr"] = ((X["tdr_p"] * X["catt"] + LG * K)
            / (X["catt"] + K))
X["ptd"] = X["attempts"] * X["tdr"]

LGI = 0.0265
X["int"] = X["attempts"] * LGI

X["pass"] = X["passing_yards"] * PY + X["ptd"] * PT
X["rush"] = X["rushing_yards"] * RY + X["rushing_tds"] * RT
X["pick"] = X["int"] * PI
X["proj"] = X["pass"] + X["rush"] + X["pick"]

B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["position"] == "QB"][
    ["player_id", "points", "exp_games", "depth_rank",
     "team"]]
X = X.merge(B, on="player_id", how="left",
            suffixes=("", "_b"))
X = X[X["depth_rank"] == 1].copy()
X = X.sort_values("proj", ascending=False)
X = X.reset_index(drop=True)
X["qbr"] = X.index + 1

REPL = float(X.iloc[9]["proj"])
X["vorp"] = X["proj"] - REPL
print("\n=== 2026 QB RANKINGS ===")
print("  10-team, 1 QB. replacement = QB10 = %.2f" % REPL)
print("  int penalty applied at league rate %.3f\n" % LGI)
print("  %-3s %-22s %-4s %5s %5s %6s %6s %6s %6s"
      % ("#", "player", "tm", "att", "tdr", "pass",
         "rush", "PROJ", "vorp"))
print("  " + "-" * 70)
for _, r in X.iterrows():
    print("  %-3d %-22s %-4s %5.1f %5.3f %6.2f %6.2f"
          " %6.2f %+6.2f"
          % (r["qbr"], str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["attempts"], r["tdr"],
             r["pass"] + r["pick"], r["rush"],
             r["proj"], r["vorp"]))

print("\n=== WHAT WAITING COSTS YOU ===")
print("  gap from each QB to the QB10 streamer")
print("  over 14 weeks\n")
for i in [0, 1, 2, 3, 4, 5, 7, 9, 11, 14]:
    if i >= len(X):
        break
    r = X.iloc[i]
    print("  QB%-2d %-22s %+5.2f ppg  %+5.0f pts"
          % (r["qbr"], str(r["player_display_name"])[:22],
             r["vorp"], r["vorp"] * 14))

W = pd.read_csv("board_final.csv", low_memory=False)
for p, lab in [("WR", "WR1"), ("RB", "RB1"),
               ("TE", "TE1")]:
    d = W[(W["position"] == p) & (W["points"] > 0)]
    d = d.sort_values("points", ascending=False)
    if len(d) > 25:
        top = float(d.iloc[0]["points"])
        rep = float(d.iloc[24]["points"])
        print("  %-4s best over 25th: %+5.2f ppg"
              % (p, top - rep))

print("\n=== YOUR SITUATION ===")
me = X[X["player_display_name"].astype(str)
       .str.contains("Caleb Williams", na=False)]
if len(me):
    r = me.iloc[0]
    print("  you roster QB%d %s at %.2f (%+.2f vorp)"
          % (r["qbr"], r["player_display_name"],
             r["proj"], r["vorp"]))
print("  CHI bye is week 10 and he is your only QB")
strm = X.iloc[9:14]
print("\n  week-10 streaming pool (QB10-14):")
for _, r in strm.iterrows():
    print("    QB%-2d %-22s %.2f"
          % (r["qbr"], str(r["player_display_name"])[:22],
             r["proj"]))
