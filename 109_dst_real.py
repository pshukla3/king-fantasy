import pandas as pd
import nflreadpy as nfl

S = pd.read_csv("league_scoring.csv")
V = dict(zip(S["key"], S["value"]))

def g(k):
    return float(V.get(k, 0.0))

PA_TIERS = [(0, 0, g("pts_allow_0")),
            (1, 6, g("pts_allow_1_6")),
            (7, 13, g("pts_allow_7_13")),
            (14, 20, g("pts_allow_14_20")),
            (21, 27, g("pts_allow_21_27")),
            (28, 34, g("pts_allow_28_34")),
            (35, 9999, g("pts_allow_35p"))]

YA_TIERS = [(0, 99, g("yds_allow_0_100")),
            (100, 199, g("yds_allow_100_199")),
            (200, 299, g("yds_allow_200_299")),
            (300, 349, g("yds_allow_300_349")),
            (350, 399, g("yds_allow_350_399")),
            (400, 449, g("yds_allow_400_449")),
            (450, 499, g("yds_allow_450_499")),
            (500, 549, g("yds_allow_500_549")),
            (550, 99999, g("yds_allow_550p"))]

print("sack %+g int %+g fum_rec %+g ff %+g safe %+g"
      % (g("sack"), g("int"), g("fum_rec"),
         g("ff"), g("safe")))

YRS = list(range(2017, 2026))
print("pulling pbp 2017-2025 ...")
P = nfl.load_pbp(seasons=YRS)
P = P.to_pandas() if hasattr(P, "to_pandas") else P
P = P[P["defteam"].notna()].copy()

def num(c):
    if c in P.columns:
        return pd.to_numeric(P[c], errors="coerce").fillna(0.0)
    return pd.Series(0.0, index=P.index)

def flag(c, val):
    if c in P.columns:
        return (P[c].astype(str) == val).astype(float)
    return pd.Series(0.0, index=P.index)

scrim = (num("rush_attempt") + num("pass_attempt")) > 0
P["_yds"] = num("yards_gained") * scrim
P["_sack"] = num("sack")
P["_int"] = num("interception")
P["_fum"] = num("fumble_lost")
P["_ff"] = num("fumble_forced")
P["_saf"] = num("safety")
P["_rtd"] = num("return_touchdown")
P["_blk"] = (num("punt_blocked")
             + flag("field_goal_result", "blocked")
             + flag("extra_point_result", "blocked"))
print("forced fumbles: %d" % int(P["_ff"].sum()))

G = P.groupby(["season", "week", "defteam"]).agg(
    sk=("_sack", "sum"), it=("_int", "sum"),
    fr=("_fum", "sum"), ff=("_ff", "sum"),
    sf=("_saf", "sum"), td=("_rtd", "sum"),
    bk=("_blk", "sum"), ya=("_yds", "sum")).reset_index()

S2 = nfl.load_schedules(seasons=YRS)
S2 = S2.to_pandas() if hasattr(S2, "to_pandas") else S2
S2 = S2[S2["game_type"] == "REG"]
S2 = S2.dropna(subset=["home_score", "away_score"])
rows = []
for _, r in S2.iterrows():
    rows.append((int(r["season"]), int(r["week"]),
                 r["home_team"], r["away_score"]))
    rows.append((int(r["season"]), int(r["week"]),
                 r["away_team"], r["home_score"]))
PA = pd.DataFrame(rows,
                  columns=["season", "week", "defteam", "pa"])
G = G.merge(PA, on=["season", "week", "defteam"], how="inner")

def tier(x, T):
    for lo, hi, v in T:
        if lo <= x <= hi:
            return v
    return T[-1][2]

G["pa_pts"] = G["pa"].map(lambda x: tier(x, PA_TIERS))
G["ya_pts"] = G["ya"].map(lambda x: tier(x, YA_TIERS))
G["dst_pts"] = (G["sk"] * g("sack") + G["it"] * g("int")
                + G["fr"] * g("fum_rec") + G["ff"] * g("ff")
                + G["sf"] * g("safe") + G["td"] * g("def_td")
                + G["bk"] * g("blk_kick")
                + G["pa_pts"] + G["ya_pts"])
G.to_csv("dst_weekly_real.csv", index=False)
print("team-games %d | mean %.2f (my wrong tiers gave 8.39)"
      % (len(G), G["dst_pts"].mean()))

T = G.groupby(["season", "defteam"])["dst_pts"].mean().reset_index()
nx = T.copy()
nx["season"] = nx["season"] - 1
nx = nx.rename(columns={"dst_pts": "next"})
M = T.merge(nx, on=["season", "defteam"], how="inner")
R = M["dst_pts"].corr(M["next"])
LG = G["dst_pts"].mean()
print("persistence r = %+.3f  (n=%d)" % (R, len(M)))

L = T[T["season"] == 2025].copy()
L["proj_2026"] = LG + R * (L["dst_pts"] - LG)
L = L.sort_values("proj_2026", ascending=False)
L = L.reset_index(drop=True)
L["rank"] = L.index + 1
L.to_csv("dst_projections_2026.csv", index=False)
print("\n=== 2026 DST, REAL LEAGUE SCORING ===")
print(L[["rank", "defteam", "dst_pts", "proj_2026"]].round(2)
      .head(14).to_string(index=False))
s = L[L["defteam"] == "SEA"]
print("\nSEA %.2f raw -> %.2f proj" % (s["dst_pts"].iloc[0],
                                       s["proj_2026"].iloc[0]))
print("replacement (11th best) %.2f" % L["proj_2026"].iloc[10])
