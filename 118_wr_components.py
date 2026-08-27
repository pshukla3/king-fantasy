import pandas as pd
import numpy as np

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"
TC = "team" if "team" in H.columns else "recent_team"

WANT = ["targets", "receptions", "receiving_yards",
        "receiving_tds", "receiving_air_yards",
        "receiving_yards_after_catch", "target_share",
        "air_yards_share", "wopr", "carries",
        "rushing_yards", "rushing_tds",
        "receiving_fumbles_lost", "attempts",
        "completions", "passing_yards", "passing_tds",
        "interceptions"]
have = [c for c in WANT if c in H.columns]
miss = [c for c in WANT if c not in H.columns]
print("rows %d | team col %s" % (len(H), TC))
print("HAVE %d: %s" % (len(have), have))
print("MISSING %d: %s" % (len(miss), miss))

def col(df, c):
    if c in df.columns:
        return pd.to_numeric(df[c], errors="coerce").fillna(0)
    return pd.Series(0.0, index=df.index)

for c in WANT:
    H["_" + c] = col(H, c)

W = H[H["position"] == "WR"].copy()
S = W.groupby(["player_id", "season"]).agg(
    g=("week", "count"),
    tgt=("_targets", "sum"),
    rec=("_receptions", "sum"),
    ryd=("_receiving_yards", "sum"),
    rtd=("_receiving_tds", "sum"),
    ay=("_receiving_air_yards", "sum"),
    yac=("_receiving_yards_after_catch", "sum"),
    car=("_carries", "sum"),
    ruyd=("_rushing_yards", "sum"),
    rutd=("_rushing_tds", "sum"),
    fl=("_receiving_fumbles_lost", "sum"),
    pts=(PC, "sum")).reset_index()
S = S[S["g"] >= 8].copy()
print("\nWR player-seasons (8+ g): %d" % len(S))

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
def g_(k):
    return float(V.get(k, 0.0))
REC, RYD, RTD = g_("rec"), g_("rec_yd"), g_("rec_td")
RUY, RUT, FUM = g_("rush_yd"), g_("rush_td"), g_("fum_lost")
print("\n=== HOW A WR SCORES IN YOUR LEAGUE ===")
print("  reception       %+.2f" % REC)
print("  receiving yard  %+.2f" % RYD)
print("  receiving TD    %+.2f" % RTD)
print("  rushing yard    %+.2f" % RUY)
print("  rushing TD      %+.2f" % RUT)
print("  fumble lost     %+.2f" % FUM)

S["rebuilt"] = (S["rec"] * REC + S["ryd"] * RYD
                + S["rtd"] * RTD + S["ruyd"] * RUY
                + S["rutd"] * RUT + S["fl"] * FUM)
S["ppg"] = S["pts"] / S["g"]
S["rb_pg"] = S["rebuilt"] / S["g"]
d = S["rb_pg"] - S["ppg"]
print("\n=== DECOMPOSITION CHECK ===")
print("  mean diff %+.3f | sd %.3f | r %.4f"
      % (d.mean(), d.std(), S["rb_pg"].corr(S["ppg"])))
print("  within 0.25 ppg of actual: %.1f%%"
      % (100.0 * (d.abs() < 0.25).mean()))

tot = S["rebuilt"].sum()
print("\n=== WHERE WR POINTS COME FROM ===")
print("  receptions  %5.1f%%"
      % (100.0 * S["rec"].sum() * REC / tot))
print("  rec yards   %5.1f%%"
      % (100.0 * S["ryd"].sum() * RYD / tot))
print("  rec TDs     %5.1f%%"
      % (100.0 * S["rtd"].sum() * RTD / tot))
print("  rushing     %5.1f%%"
      % (100.0 * (S["ruyd"].sum() * RUY
                  + S["rutd"].sum() * RUT) / tot))

S["tpg"] = S["tgt"] / S["g"]
S["catch_rate"] = S["rec"] / S["tgt"].replace(0, np.nan)
S["ypc"] = S["ryd"] / S["rec"].replace(0, np.nan)
S["ypt"] = S["ryd"] / S["tgt"].replace(0, np.nan)
S["adot"] = S["ay"] / S["tgt"].replace(0, np.nan)
S["yac_pc"] = S["yac"] / S["rec"].replace(0, np.nan)
S["td_rate"] = S["rtd"] / S["tgt"].replace(0, np.nan)

tt = H.groupby([TC, "season"]).agg(
    tm_tgt=("_targets", "sum"),
    tm_att=("_attempts", "sum"),
    tm_cmp=("_completions", "sum"),
    tm_pyd=("_passing_yards", "sum"),
    tm_ptd=("_passing_tds", "sum"),
    tm_int=("_interceptions", "sum")).reset_index()
gm = H.groupby([TC, "season"])["week"].nunique()
tt = tt.merge(gm.rename("tm_g").reset_index(),
              on=[TC, "season"])

def cl(x):
    return np.clip(x, 0.0, 2.375)
at = tt["tm_att"].replace(0, np.nan)
a = cl((tt["tm_cmp"] / at - 0.3) * 5.0)
b = cl((tt["tm_pyd"] / at - 3.0) * 0.25)
c = cl((tt["tm_ptd"] / at) * 20.0)
e = cl(2.375 - (tt["tm_int"] / at) * 25.0)
tt["passer_rtg"] = (a + b + c + e) / 6.0 * 100.0
tt["tm_att_pg"] = tt["tm_att"] / tt["tm_g"]
tt["tm_pyd_pg"] = tt["tm_pyd"] / tt["tm_g"]
print("\nteam-seasons: %d | passer rtg %.1f to %.1f"
      % (len(tt), tt["passer_rtg"].min(),
         tt["passer_rtg"].max()))

nm = H.sort_values(["season", "week"]).groupby(
    ["player_id", "season"]).tail(1)[
    ["player_id", "season", "player_display_name", TC]]
S = S.merge(nm, on=["player_id", "season"], how="left")
S = S.merge(tt, on=[TC, "season"], how="left")
S["tgt_share"] = S["tgt"] / S["tm_tgt"].replace(0, np.nan)
S.to_csv("wr_components.csv", index=False)
print("Saved wr_components.csv (%d rows)" % len(S))

L = S[S["season"] == 2025].nlargest(40, "ppg")
print("\n=== 2025 WR COMPONENTS, top 40 ===")
print("  %-21s %-4s %5s %5s %5s %5s %5s %5s %5s %5s"
      % ("player", "tm", "ppg", "tgt/g", "cat%", "ypc",
         "aDOT", "tdrt", "shr", "QBrt"))
for _, r in L.iterrows():
    print("  %-21s %-4s %5.1f %5.1f %5.1f %5.1f %5.1f "
          "%5.3f %5.3f %5.1f"
          % (str(r["player_display_name"])[:21], r[TC],
             r["ppg"], r["tpg"], 100 * r["catch_rate"],
             r["ypc"], r["adot"], r["td_rate"],
             r["tgt_share"], r["passer_rtg"]))
