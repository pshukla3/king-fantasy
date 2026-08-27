import pandas as pd, re
import nflreadpy as nfl

d = nfl.load_depth_charts(seasons=[2026])
d = d.to_pandas() if hasattr(d, "to_pandas") else d
print("raw rows: %d | teams: %d" % (len(d), d["team"].nunique()))
print("dt:  %s  ->  %s" % (d["dt"].min(), d["dt"].max()))
print("\npos_grp: %s" % d["pos_grp"].value_counts().to_dict())
print("\npos_abb top: %s" % d["pos_abb"].value_counts().head(14).to_dict())
print("\npos_rank vals: %s" % sorted(d["pos_rank"].dropna().unique())[:12])
print("pos_slot sample: %s" % sorted(d["pos_slot"].dropna().astype(str).unique())[:16])

d["_mx"] = d.groupby("team")["dt"].transform("max")
D = d[d["dt"] == d["_mx"]].copy()
D["pos_rank"] = pd.to_numeric(D["pos_rank"], errors="coerce")
D["pos_abb"] = D["pos_abb"].astype(str).str.upper()
print("\nlatest snapshot: %d rows across %d teams" % (len(D), D["team"].nunique()))
D.to_csv("depth_latest.csv", index=False)
print("Saved depth_latest.csv")

OFF = ["QB", "RB", "FB", "WR", "TE", "K"]

print("\n\n%s" % ("=" * 58))
print("SEATTLE SEAHAWKS — 2026 DEPTH CHART (latest snapshot)")
print("=" * 58)
S = D[D["team"].astype(str).str.upper() == "SEA"]
for pos in OFF:
    g = S[S["pos_abb"] == pos].sort_values("pos_rank")
    if not len(g):
        continue
    print("\n  %s" % pos)
    for _, r in g.iterrows():
        rk = r["pos_rank"]
        slot = str(r["pos_slot"])
        print("    %-2s  %-26s %s"
              % ("%.0f" % rk if rk == rk else "-", r["player_name"],
                 slot if slot != "nan" else ""))

s1 = D[(D["pos_rank"] == 1) & D["pos_abb"].isin(OFF)].copy()
s1[["gsis_id", "player_name", "team", "pos_abb", "pos_slot"]].to_csv(
    "starters_2026.csv", index=False)
print("\n\n=== pos_rank == 1 COUNTS, ALL TEAMS ===")
print(s1["pos_abb"].value_counts().reindex(OFF).dropna().to_string())

def norm(x):
    return re.sub(r"[^a-z]", "", str(x).lower())
D["k_"] = D["player_name"].map(norm)

mine = ["Caleb Williams", "Omarion Hampton", "Bhayshul Tuten", "Jaxon Smith-Njigba",
        "George Pickens", "Kyle Pitts", "Tee Higgins", "Josh Downs",
        "TreVeyon Henderson", "Rico Dowdle", "Keaton Mitchell", "Deebo Samuel",
        "Rashid Shaheed", "Harrison Butker"]
print("\n=== YOUR ROSTER: STARTER CHECK ===")
for nm in mine:
    h = D[D["k_"].str.contains(norm(nm), na=False) & D["pos_abb"].isin(OFF)]
    if not len(h):
        print("  %-22s  NOT ON ANY DEPTH CHART" % nm)
        continue
    r = h.sort_values("pos_rank").iloc[0]
    o = r["pos_rank"]
    tag = ("STARTER" if o == 1 else "2nd string" if o == 2
           else "3rd string" if o == 3 else "buried")
    slot = str(r["pos_slot"])
    print("  %-22s  %-4s %-3s %-7s rank %s   %s"
          % (nm, r["team"], r["pos_abb"], slot if slot != "nan" else "",
             "%.0f" % o if o == o else "?", tag))
