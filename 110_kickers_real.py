import pandas as pd
import nflreadpy as nfl

S = pd.read_csv("league_scoring.csv")
V = dict(zip(S["key"], S["value"]))

def g(k):
    return float(V.get(k, 0.0))

BANDS = [(0, 19, g("fgm_0_19")),
         (20, 29, g("fgm_20_29")),
         (30, 39, g("fgm_30_39")),
         (40, 49, g("fgm_40_49")),
         (50, 999, g("fgm_50p"))]
FGMISS = g("fgmiss")
XPM = g("xpm")
XPMISS = g("xpmiss")
for lo, hi, v in BANDS:
    print("  FG %3d-%-3d  %+g" % (lo, hi, v))
print("  fgmiss %+g | xpm %+g | xpmiss %+g"
      % (FGMISS, XPM, XPMISS))

YRS = [2023, 2024, 2025]
print("pulling pbp ...")
P = nfl.load_pbp(seasons=YRS)
P = P.to_pandas() if hasattr(P, "to_pandas") else P
KN = "kicker_player_name"
print("pbp rows: %d" % len(P))

FG = P[(pd.to_numeric(P["field_goal_attempt"],
                      errors="coerce") == 1)
       & P[KN].notna()].copy()
FG["dist"] = pd.to_numeric(FG["kick_distance"], errors="coerce")
FG = FG.dropna(subset=["dist"])
FG["made"] = (FG["field_goal_result"] == "made").astype(int)

def fgpts(r):
    if not r["made"]:
        return FGMISS
    for lo, hi, v in BANDS:
        if lo <= r["dist"] <= hi:
            return v
    return BANDS[-1][2]

FG["pts"] = FG.apply(fgpts, axis=1)
print("FG att %d | made %d | net pts %.0f"
      % (len(FG), int(FG["made"].sum()), FG["pts"].sum()))

XP = P[(pd.to_numeric(P["extra_point_attempt"],
                      errors="coerce") == 1)
       & P[KN].notna()].copy()
XP["res"] = XP["extra_point_result"].astype(str)
XP["made"] = (XP["res"] == "good").astype(int)
XP["miss"] = XP["res"].isin(["failed", "blocked"]).astype(int)
XP["pts"] = XP["made"] * XPM + XP["miss"] * XPMISS
print("XP att %d | made %d | missed %d"
      % (len(XP), int(XP["made"].sum()), int(XP["miss"].sum())))

A = pd.concat([FG[[KN, "game_id", "pts"]],
               XP[[KN, "game_id", "pts"]]], ignore_index=True)
K = A.groupby(KN).agg(pts=("pts", "sum"),
                      gms=("game_id", "nunique")).reset_index()
f = FG.groupby(KN).agg(fga=("made", "size"),
                       fgm=("made", "sum")).reset_index()
x = XP.groupby(KN).agg(xpa=("made", "size"),
                       xpm=("made", "sum")).reset_index()
K = K.merge(f, on=KN, how="left").merge(x, on=KN, how="left")
K = K.fillna(0)
K["ppg"] = K["pts"] / K["gms"]
K["fg_pct"] = K["fgm"] / K["fga"].replace(0, float("nan"))
K = K[K["gms"] >= 16].sort_values("ppg", ascending=False)
K = K.reset_index(drop=True)
K["rank"] = K.index + 1
K = K.rename(columns={KN: "kicker"})
K.to_csv("kicker_projections.csv", index=False)

C = ["rank", "kicker", "gms", "fga", "fgm", "fg_pct",
     "xpa", "xpm", "ppg"]
print("\n=== KICKERS, REAL SCORING (min 16 g) ===")
print(K.head(20)[C].round(2).to_string(index=False))
repl = float(K["ppg"].iloc[10])
print("\nreplacement (11th) %.2f  (old wrong value 9.10)" % repl)
b = K[K["kicker"].astype(str).str.contains("Butker", na=False)]
if len(b):
    print("Butker %.2f ppg  %+.2f vs repl"
          % (b["ppg"].iloc[0], b["ppg"].iloc[0] - repl))
