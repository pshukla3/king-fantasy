import json
import nflreadpy as nfl
import pandas as pd

YR = [2023, 2024, 2025, 2026]
print("loading play-by-play (this takes a minute)")
p = nfl.load_pbp(YR).to_pandas()
p = p[(p["play_type"] == "run") & p["posteam"].notna()]
p = p[p["yardline_100"].notna()]

gl = p[p["yardline_100"] <= 3].copy()
gl["isqb"] = (gl["rusher_player_id"].notna()
              & gl["passer_player_id"].isna()
              & gl["qb_dropback"].fillna(0).eq(0)
              & gl["rusher_player_name"].notna())

# a team's QB share of carries inside the 3
qb = nfl.load_player_stats(YR).to_pandas()
QBIDS = set(qb[qb["position"] == "QB"]["player_id"].unique())
gl["qbrun"] = gl["rusher_player_id"].isin(QBIDS)

t = gl.groupby("posteam").agg(
    n=("qbrun", "size"), qbn=("qbrun", "sum"),
    td=("rush_touchdown", "sum")).reset_index()
t["qbshare"] = t["qbn"] / t["n"]
t = t.sort_values("qbshare", ascending=False)

print("\n=== QB SHARE OF CARRIES INSIDE THE 3 ===")
print("  %-5s %7s %7s %9s" % ("TEAM", "PLAYS", "QB", "QB SHARE"))
for _, r in t.head(8).iterrows():
    print("  %-5s %7d %7d %8.1f%%"
          % (r["posteam"], r["n"], r["qbn"], r["qbshare"] * 100))
print("  ...")
for _, r in t.tail(4).iterrows():
    print("  %-5s %7d %7d %8.1f%%"
          % (r["posteam"], r["n"], r["qbn"], r["qbshare"] * 100))

PUSH = set(t[t["qbshare"] >= 0.45]["posteam"])
print("\ntush-push teams (QB >=45%% inside 3): %s"
      % ", ".join(sorted(PUSH)))

# what it costs the RB
rb = gl[~gl["qbrun"]].copy()
rb["push"] = rb["posteam"].isin(PUSH)
a = rb[rb["push"]]
b = rb[~rb["push"]]
print("\n=== RB CARRIES INSIDE THE 3, per team-game ===")
ga = a.groupby(["season", "week", "posteam"]).size()
gb = b.groupby(["season", "week", "posteam"]).size()
print("  tush-push teams : %.2f RB carries/gm  TD rate %.3f"
      % (ga.mean(), a["rush_touchdown"].mean()))
print("  everyone else   : %.2f RB carries/gm  TD rate %.3f"
      % (gb.mean(), b["rush_touchdown"].mean()))
supp = ga.mean() / gb.mean()
print("  -> RB goal-line volume multiplier: %.3f" % supp)

OUT = {"push_teams": sorted(PUSH),
       "rb_gl_mult": round(float(supp), 4),
       "qb_share": {r["posteam"]: round(r["qbshare"], 4)
                    for _, r in t.iterrows()}}
json.dump(OUT, open("tushpush.json", "w"), indent=1)
print("\nwrote tushpush.json")

print("\n=== RB rushing TDs per game, push vs not ===")
s = nfl.load_player_stats(YR).to_pandas()
s = s[(s["position"] == "RB") & (s["carries"] >= 8)]
s["push"] = s["team"].isin(PUSH)
print("  tush-push teams : %.3f rush TD/gm (n=%d)"
      % (s[s["push"]]["rushing_tds"].mean(),
         len(s[s["push"]])))
print("  everyone else   : %.3f rush TD/gm (n=%d)"
      % (s[~s["push"]]["rushing_tds"].mean(),
         len(s[~s["push"]])))
