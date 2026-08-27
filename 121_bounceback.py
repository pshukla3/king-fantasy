import pandas as pd
import numpy as np

C = pd.read_csv("wr_components.csv")
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
RTD = float(V.get("rec_td", 6.0))

C = C[(C["tgt"] > 0) & (C["g"] > 0)].copy()
g = C.groupby("season")[["rtd", "tgt"]].sum()
g["lg_tdr"] = g["rtd"] / g["tgt"]
LG = g[["lg_tdr"]].reset_index()
C = C.merge(LG, on="season", how="left")
C["exp_td"] = C["tgt"] * C["lg_tdr"]
C["td_luck"] = C["rtd"] - C["exp_td"]

N = C[["player_id", "season", "ppg"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"ppg": "ppg_n"})
P = C.merge(N, on=["player_id", "season"], how="inner")

print("league WR TD per target, by season:")
print(LG.round(4).to_string(index=False))
print("\nWR year N -> N+1 pairs: %d" % len(P))

yrs = sorted(P["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = P[P["season"] < cut].copy()
TE = P[P["season"] >= cut].copy()
print("\ntrain < %d  n=%d" % (cut, len(TR)))
print("test >= %d  n=%d" % (cut, len(TE)))

def adj(d, w):
    return d["ppg"] - w * d["td_luck"] * RTD / d["g"]

bw, br = 0.0, -1.0
for i in range(21):
    w = i / 20.0
    r = adj(TR, w).corr(TR["ppg_n"])
    if r > br:
        bw, br = w, r
print("\nbest weight on TD regression = %.2f" % bw)
print("  (1.00 = throw away his TDs entirely)")
print("  train r %.3f" % br)

rraw = TE["ppg"].corr(TE["ppg_n"])
rfit = adj(TE, bw).corr(TE["ppg_n"])
print("\n=== OUT OF SAMPLE ===")
print("  raw ppg baseline   r %.3f" % rraw)
print("  TD-regressed       r %.3f" % rfit)
print("  gain               %+.3f" % (rfit - rraw))
print("  pre-declared adopt threshold: +0.010")
print("  DECISION: %s"
      % ("ADOPT" if rfit - rraw > 0.010 else "REJECT"))

L = C[(C["season"] == 2025) & (C["g"] >= 10)].copy()
L["bounce"] = -bw * L["td_luck"] * RTD / L["g"]
L["ppg_adj"] = L["ppg"] + L["bounce"]

def show(d, title):
    print("\n=== %s ===" % title)
    print("  %-21s %-4s %5s %5s %5s %6s %6s"
          % ("player", "tm", "ppg", "td", "exp",
             "bounce", "adj"))
    for _, r in d.iterrows():
        print("  %-21s %-4s %5.1f %5.0f %5.1f %+6.2f %6.1f"
              % (str(r["player_display_name"])[:21],
                 r["team"], r["ppg"], r["rtd"],
                 r["exp_td"], r["bounce"], r["ppg_adj"]))

show(L.nsmallest(12, "bounce"),
     "TD-INFLATED - model is too high")
show(L.nlargest(12, "bounce"),
     "TD-STARVED - bounceback candidates")

NM = ["Rashee Rice", "A.J. Brown", "Ladd McConkey",
      "Ja'Marr Chase", "Puka Nacua", "Tee Higgins",
      "George Pickens", "Jaxon Smith-Njigba"]
show(L[L["player_display_name"].isin(NM)]
     .sort_values("bounce"), "YOUR NAMES")

L.to_csv("wr_bounceback.csv", index=False)
print("\nSaved wr_bounceback.csv")
