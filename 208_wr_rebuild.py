import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
W = pl(nfl.load_player_stats(seasons=list(range(2019, 2026))))
for c in ["targets", "receptions", "receiving_yards",
          "receiving_tds"]:
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
W["team"] = W["team"].astype(str).replace(FIX)
W = W[W["position"].isin(["WR", "TE", "RB"])].copy()

TT = W.groupby(["team", "season"]).agg(
    ttar=("targets", "sum"),
    tg=("week", "nunique")).reset_index()
TT["ttpg"] = TT["ttar"] / TT["tg"]

S = W.groupby(["player_id", "season", "team",
               "position"]).agg(
    tar=("targets", "sum"), rec=("receptions", "sum"),
    yds=("receiving_yards", "sum"),
    td=("receiving_tds", "sum"),
    g=("week", "nunique")).reset_index()
S = S.merge(TT[["team", "season", "ttpg"]],
            on=["team", "season"], how="left")
S = S[(S["g"] >= 6) & (S["ttpg"] > 0)].copy()
S["tpg"] = S["tar"] / S["g"]
S["share"] = S["tpg"] / S["ttpg"]
S.to_csv("wr_shares.csv", index=False)

N = S[["player_id", "season", "team", "tpg",
       "share"]].copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"tpg": "n_tpg", "share": "n_share",
                      "team": "n_team"})
P = S.merge(N, on=["player_id", "season"], how="inner")
P["moved"] = P["team"] != P["n_team"]

print("=== DOES SHARE TRAVEL BETTER THAN VOLUME? ===")
print("  predicting next season from this one\n")
print("  %-12s %6s %12s %12s"
      % ("group", "n", "tar/g r", "share r"))
for lab, d in [("stayed", P[~P["moved"]]),
               ("CHANGED TEAM", P[P["moved"]]),
               ("all", P)]:
    if len(d) < 20:
        continue
    print("  %-12s %6d %12.3f %12.3f"
          % (lab, len(d), d["tpg"].corr(d["n_tpg"]),
             d["share"].corr(d["n_share"])))

V = TT[TT["season"] >= 2020].copy()
NV = V.copy()
NV["season"] = NV["season"] - 1
NV = NV.rename(columns={"ttpg": "nx"})[
    ["team", "season", "nx"]]
PV = V.merge(NV, on=["team", "season"], how="inner")
RV = float(PV["ttpg"].corr(PV["nx"]))
LGV = float(V["ttpg"].mean())
print("\n=== TEAM TARGET VOLUME ===")
print("  persistence r = %+.3f | league mean %.1f tar/g"
      % (RV, LGV))
T25 = TT[TT["season"] == 2025][["team", "ttpg"]].copy()
T25["v26"] = LGV + RV * (T25["ttpg"] - LGV)
TEAMV = dict(zip(T25["team"], T25["v26"]))
print("  2026 projected range %.1f to %.1f"
      % (T25["v26"].min(), T25["v26"].max()))

DEC = 0.5
S["w"] = DEC ** (2025 - S["season"])
S = S[S["season"] >= 2021]
A = S.groupby("player_id").apply(
    lambda d: pd.Series({
        "wtar": float((d["w"] * d["tar"]).sum()),
        "wg": float((d["w"] * d["g"]).sum()),
        "wsh": float((d["w"] * d["tar"] * d["share"]).sum()),
        "wrec": float((d["w"] * d["rec"]).sum()),
        "wyds": float((d["w"] * d["yds"]).sum()),
        "wtd": float((d["w"] * d["td"]).sum()),
        "tot_tar": float(d["tar"].sum())}),
    include_groups=False).reset_index()
A["raw_share"] = A["wsh"] / A["wtar"].replace(0, np.nan)

BASE = S[S["tar"] >= 20]
LO = float(BASE["share"].quantile(0.25))
CT = float(BASE["rec"].sum() / BASE["tar"].sum())
YR = float(BASE["yds"].sum() / BASE["rec"].sum())
TR = float(BASE["td"].sum() / BASE["rec"].sum())
print("=== PRIORS ===")
print("  low-share prior %.4f | catch%% %.3f"
      % (LO, CT))
print("  yds/rec %.2f | td/rec %.4f" % (YR, TR))

KS, KE = 120.0, 90.0
A["score"] = ((A["wsh"] + KS * LO)
              / (A["wtar"] + KS))
A["ctch"] = ((A["wrec"] + KE * CT)
             / (A["wtar"] + KE))
A["ypr"] = ((A["wyds"] + KE * 3.0 * YR)
            / (A["wrec"] + KE * 3.0))
A["tdr"] = ((A["wtd"] + KE * 3.0 * TR)
            / (A["wrec"] + KE * 3.0))

B = pd.read_csv("board_final.csv", low_memory=False)
B["team"] = B["team"].astype(str).replace(FIX)
C = B[B["position"].isin(["WR", "TE", "RB"])].copy()
C = C.merge(A, on="player_id", how="left")
for c, v in [("score", LO * 0.55), ("ctch", CT),
             ("ypr", YR), ("tdr", TR)]:
    C[c] = C[c].fillna(v)

POOL = 0.95
C["tv"] = C["team"].map(TEAMV).fillna(LGV)
tot = C.groupby("team")["score"].transform("sum")
C["alloc"] = C["score"] / tot.replace(0, np.nan) * POOL
C["tar26"] = C["alloc"] * C["tv"]
C["rec26"] = C["tar26"] * C["ctch"]
C["ppg26"] = C["rec26"] * (1.0 + 0.1 * C["ypr"]
                           + 6.0 * C["tdr"])
C.to_csv("wr_rebuild_2026.csv", index=False)
print("\npass-catchers allocated: %d" % len(C))
print("  teams %d | mean tar/g check %.1f"
      % (C["team"].nunique(),
         C.groupby("team")["tar26"].sum().mean()))

DEC = 0.5
S["w"] = DEC ** (2025 - S["season"])
S = S[S["season"] >= 2021]
A = S.groupby("player_id").apply(
    lambda d: pd.Series({
        "wtar": float((d["w"] * d["tar"]).sum()),
        "wg": float((d["w"] * d["g"]).sum()),
        "wsh": float((d["w"] * d["tar"] * d["share"]).sum()),
        "wrec": float((d["w"] * d["rec"]).sum()),
        "wyds": float((d["w"] * d["yds"]).sum()),
        "wtd": float((d["w"] * d["td"]).sum()),
        "tot_tar": float(d["tar"].sum())}),
    include_groups=False).reset_index()
A["raw_share"] = A["wsh"] / A["wtar"].replace(0, np.nan)

BASE = S[S["tar"] >= 20]
LO = float(BASE["share"].quantile(0.25))
CT = float(BASE["rec"].sum() / BASE["tar"].sum())
YR = float(BASE["yds"].sum() / BASE["rec"].sum())
TR = float(BASE["td"].sum() / BASE["rec"].sum())
print("=== PRIORS ===")
print("  low-share prior %.4f | catch%% %.3f"
      % (LO, CT))
print("  yds/rec %.2f | td/rec %.4f" % (YR, TR))

KS, KE = 120.0, 90.0
A["score"] = ((A["wsh"] + KS * LO)
              / (A["wtar"] + KS))
A["ctch"] = ((A["wrec"] + KE * CT)
             / (A["wtar"] + KE))
A["ypr"] = ((A["wyds"] + KE * 3.0 * YR)
            / (A["wrec"] + KE * 3.0))
A["tdr"] = ((A["wtd"] + KE * 3.0 * TR)
            / (A["wrec"] + KE * 3.0))

B = pd.read_csv("board_final.csv", low_memory=False)
B["team"] = B["team"].astype(str).replace(FIX)
C = B[B["position"].isin(["WR", "TE", "RB"])].copy()
C = C.merge(A, on="player_id", how="left")
for c, v in [("score", LO * 0.55), ("ctch", CT),
             ("ypr", YR), ("tdr", TR)]:
    C[c] = C[c].fillna(v)

POOL = 0.95
C["tv"] = C["team"].map(TEAMV).fillna(LGV)
tot = C.groupby("team")["score"].transform("sum")
C["alloc"] = C["score"] / tot.replace(0, np.nan) * POOL
C["tar26"] = C["alloc"] * C["tv"]
C["rec26"] = C["tar26"] * C["ctch"]
C["ppg26"] = C["rec26"] * (1.0 + 0.1 * C["ypr"]
                           + 6.0 * C["tdr"])
C.to_csv("wr_rebuild_2026.csv", index=False)
print("\npass-catchers allocated: %d" % len(C))
print("  teams %d | mean tar/g check %.1f"
      % (C["team"].nunique(),
         C.groupby("team")["tar26"].sum().mean()))

WR = C[C["position"] == "WR"].copy()
WR["old"] = pd.to_numeric(WR["points"], errors="coerce")
WR = WR[WR["ppg26"].notna()].sort_values(
    "ppg26", ascending=False).reset_index(drop=True)
WR["mv"] = WR["ppg26"] - WR["old"]

print("=== 2026 WR RANKINGS, OPPORTUNITY x EFFICIENCY ===")
print("  targets from the NEW team and depth chart")
print("  efficiency from the player's own history\n")
print("  %-3s %-22s %-4s %6s %6s %6s %7s %7s %7s"
      % ("#", "player", "tm", "tar/g", "rec/g",
         "yd/rec", "NEW", "old", "move"))
print("  " + "-" * 78)
for i, r in WR.head(40).iterrows():
    o = r["old"]
    print("  %-3d %-22s %-4s %6.1f %6.1f %6.1f %7.2f %7s %+7s"
          % (i + 1, str(r["player_display_name"])[:22],
             str(r["team"])[:4], r["tar26"], r["rec26"],
             r["ypr"], r["ppg26"],
             "--" if o != o else "%.2f" % o,
             "--" if o != o else "%.2f" % (r["ppg26"] - o)))

print("\n=== THE SITUATION MOVERS ===")
for nm in ["Jaylen Waddle", "A.J. Brown", "Xavier Worthy",
           "Jaxon Smith-Njigba", "Deebo Samuel",
           "Davante Adams", "Stefon Diggs"]:
    h = WR[WR["player_display_name"].astype(str)
           .str.contains(nm.split()[-1], na=False)
           & WR["player_display_name"].astype(str)
           .str.contains(nm.split()[0][0], na=False)]
    h = h[h["player_display_name"] == nm]
    if not len(h):
        print("  %-22s not found" % nm)
        continue
    r = h.iloc[0]
    o = r["old"]
    print("  %-22s %-4s tar/g %4.1f | %6.2f -> %6.2f  %s"
          % (nm[:22], str(r["team"])[:4], r["tar26"],
             0 if o != o else o, r["ppg26"],
             "" if o != o
             else "%+.2f" % (r["ppg26"] - o)))

print("\n=== TEAM ROOMS, THE TWO YOU FLAGGED ===")
for tm in ["DEN", "NE"]:
    d = C[C["team"] == tm].nlargest(6, "ppg26")
    print("\n  %s target allocation:" % tm)
    for _, x in d.iterrows():
        print("    %-24s %-3s %5.1f tar/g  %6.2f ppg"
              % (str(x["player_display_name"])[:24],
                 x["position"], x["tar26"], x["ppg26"]))
