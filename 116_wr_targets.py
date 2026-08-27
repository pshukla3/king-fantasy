import pandas as pd
import numpy as np

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"
TC = "team" if "team" in H.columns else "recent_team"
need = ["player_id", "position", "season", "week",
        "targets", "receiving_yards", "receiving_tds", PC]
miss = [c for c in need if c not in H.columns]
print("rows %d | team col %s" % (len(H), TC))
print("missing cols: %s" % miss)

H["targets"] = pd.to_numeric(
    H["targets"], errors="coerce").fillna(0)
tt = H.groupby([TC, "season", "week"])["targets"].sum()
tt = tt.rename("tm_tgt").reset_index()

W = H[H["position"] == "WR"].copy()
W = W.merge(tt, on=[TC, "season", "week"], how="left")
print("WR player-weeks: %d" % len(W))

S = W.groupby(["player_id", "season"]).agg(
    g=("week", "count"),
    tgt=("targets", "sum"),
    tmt=("tm_tgt", "sum"),
    ryd=("receiving_yards", "sum"),
    rtd=("receiving_tds", "sum"),
    pts=(PC, "sum")).reset_index()
S = S[S["g"] >= 8].copy()
S["share"] = S["tgt"] / S["tmt"].replace(0, np.nan)
S["ypt"] = S["ryd"] / S["tgt"].replace(0, np.nan)
S["tdr"] = S["rtd"] / S["tgt"].replace(0, np.nan)
S["ppg"] = S["pts"] / S["g"]
S["tpg"] = S["tgt"] / S["g"]
print("\nWR player-seasons (8+ g): %d" % len(S))
print("target share: %.3f to %.3f, mean %.3f"
      % (S["share"].min(), S["share"].max(),
         S["share"].mean()))

N = S.copy()
N["season"] = N["season"] - 1
N = N[["player_id", "season", "share", "ypt", "tdr",
       "ppg", "tpg"]].rename(columns={
    "share": "share_n", "ypt": "ypt_n", "tdr": "tdr_n",
    "ppg": "ppg_n", "tpg": "tpg_n"})
P = S.merge(N, on=["player_id", "season"], how="inner")
print("year N -> N+1 WR pairs: %d" % len(P))
P.to_csv("wr_pairs.csv", index=False)

print("\n=== WHAT PERSISTS FOR WRs? (N vs N+1) ===")
for c, lbl in [("share", "target share"),
               ("tpg", "targets per game"),
               ("ypt", "yards per target"),
               ("tdr", "TD per target"),
               ("ppg", "fantasy ppg")]:
    print("  %-18s r = %+.3f"
          % (lbl, P[c].corr(P[c + "_n"])))

print("\n=== WHAT PREDICTS NEXT-YEAR PPG? ===")
for c, lbl in [("ppg", "his own ppg"),
               ("share", "his target share"),
               ("tpg", "his targets/game"),
               ("ypt", "his yards/target")]:
    print("  %-18s r = %+.3f"
          % (lbl, P[c].corr(P["ppg_n"])))

P["eff"] = P["ppg"] / P["tpg"].replace(0, np.nan)
LG = P["tpg"].mean()
P["role_ppg"] = P["eff"] * LG
P["share_ppg"] = P["eff"] * P["tpg"]

print("\n=== BLEND TEST: flat role average vs raw ppg ===")
print("  league-average WR targets/game = %.2f" % LG)
bw, br = 0.0, -1.0
for i in range(21):
    w = i / 20.0
    b = w * P["role_ppg"] + (1 - w) * P["ppg"]
    r = b.corr(P["ppg_n"])
    if r > br:
        bw, br = w, r
print("  best weight on flat role = %.2f  (r %.3f)" % (bw, br))
print("  engine currently uses     0.60")
print("  raw ppg alone             r %.3f"
      % P["ppg"].corr(P["ppg_n"]))
