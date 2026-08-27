import pandas as pd
import numpy as np

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"
TC = "team" if "team" in H.columns else "recent_team"

for c in ["targets", "receiving_air_yards"]:
    H[c] = pd.to_numeric(H[c], errors="coerce").fillna(0)

tm = H.groupby([TC, "season", "week"]).agg(
    tm_tgt=("targets", "sum"),
    tm_ay=("receiving_air_yards", "sum")).reset_index()

W = H[H["position"] == "WR"].copy()
W = W.merge(tm, on=[TC, "season", "week"], how="left")

S = W.groupby(["player_id", "season"]).agg(
    g=("week", "count"),
    tgt=("targets", "sum"),
    ay=("receiving_air_yards", "sum"),
    tmt=("tm_tgt", "sum"),
    tma=("tm_ay", "sum"),
    pts=(PC, "sum")).reset_index()
S = S[(S["g"] >= 8) & (S["tmt"] > 0) & (S["tma"] > 0)]

S["tgt_sh"] = S["tgt"] / S["tmt"]
S["ay_sh"] = S["ay"] / S["tma"]
S["wopr"] = 1.5 * S["tgt_sh"] + 0.7 * S["ay_sh"]
S["ppg"] = S["pts"] / S["g"]

print("WR seasons: %d" % len(S))
print("first season with air yards: %d"
      % int(S[S["ay"] > 0]["season"].min()))
print("WOPR %.3f to %.3f, mean %.3f"
      % (S["wopr"].min(), S["wopr"].max(),
         S["wopr"].mean()))

N = S[["player_id", "season", "ppg", "tgt_sh",
       "ay_sh", "wopr"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "ppg_n", "tgt_sh": "ts_n",
                      "ay_sh": "as_n", "wopr": "wopr_n"})
P = S.merge(N, on=["player_id", "season"], how="inner")
P = P.dropna(subset=["ppg", "ppg_n", "wopr"])
print("\nWR N -> N+1 pairs: %d" % len(P))

print("\n=== PERSISTENCE (N vs N+1) ===")
for a, b, lb in [("tgt_sh", "ts_n", "target share"),
                 ("ay_sh", "as_n", "air yards share"),
                 ("wopr", "wopr_n", "WOPR"),
                 ("ppg", "ppg_n", "fantasy ppg")]:
    print("  %-17s r = %+.3f" % (lb, P[a].corr(P[b])))

print("\n=== PREDICTS NEXT-YEAR PPG ===")
for c, lb in [("ppg", "his own ppg"),
              ("tgt_sh", "target share"),
              ("ay_sh", "air yards share"),
              ("wopr", "WOPR")]:
    print("  %-17s r = %+.3f"
          % (lb, P[c].corr(P["ppg_n"])))
print("\n  published benchmark: WOPR, ay_sh, tgt_sh")
print("  all above 0.70 on both axes")

yrs = sorted(P["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = P[P["season"] < cut].copy()
TE = P[P["season"] >= cut].copy()
print("\ntrain < %d  n=%d" % (cut, len(TR)))
print("test >= %d  n=%d" % (cut, len(TE)))

def ols(x, y):
    b = x.cov(y) / x.var()
    return y.mean() - b * x.mean(), b

a1, b1 = ols(TR["wopr"], TR["ppg_n"])
print("\ntrain fit: ppg_next = %.2f + %.2f x WOPR"
      % (a1, b1))
wp_tr = a1 + b1 * TR["wopr"]
wp_te = a1 + b1 * TE["wopr"]

bw, br = 0.0, -1.0
for i in range(21):
    w = i / 20.0
    r = (w * wp_tr + (1 - w) * TR["ppg"]).corr(TR["ppg_n"])
    if r > br:
        bw, br = w, r
print("best weight on WOPR = %.2f (train r %.3f)"
      % (bw, br))

rraw = TE["ppg"].corr(TE["ppg_n"])
rw = wp_te.corr(TE["ppg_n"])
rb = (bw * wp_te + (1 - bw) * TE["ppg"]).corr(TE["ppg_n"])
gain = max(rw, rb) - rraw

print("\n=== OUT OF SAMPLE ===")
print("  raw ppg baseline   r %.3f" % rraw)
print("  WOPR alone         r %.3f" % rw)
print("  blended            r %.3f" % rb)
print("  best gain          %+.3f" % gain)
print("  threshold          +0.010")
print("  DECISION: %s"
      % ("ADOPT" if gain > 0.010 else "REJECT"))
P.to_csv("wr_wopr_pairs.csv", index=False)
print("\nSaved wr_wopr_pairs.csv")
