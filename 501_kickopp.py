import json
import numpy as np
import nflreadpy as nfl

YR = [2024, 2025, 2026]
print("loading pbp")
p = nfl.load_pbp(YR).to_pandas()
p = p[p["posteam"].notna()]

# one row per drive
dv = p.groupby(["season", "week", "posteam", "defteam",
                "drive"], as_index=False).agg(
    res=("fixed_drive_result", "first"),
    best=("yardline_100", "min"))
dv = dv[dv["res"].notna()]
dv["td"] = dv["res"].str.contains("Touchdown", na=False)
dv["fg"] = dv["res"].str.contains("Field goal", na=False)
dv["miss"] = dv["res"].str.contains("Missed", na=False)
dv["att"] = dv["fg"] | dv["miss"]
dv["inrange"] = dv["best"] <= 40      # reached opp 40
dv["rz"] = dv["best"] <= 20

print("drives: %d  (%s-%s)"
      % (len(dv), dv["season"].min(), dv["season"].max()))

def tbl(key, label, yrs):
    d = dv[dv["season"].isin(yrs)]
    g = d.groupby(key, as_index=False).agg(
        dr=("drive", "size"),
        gm=("week", lambda s: s.nunique() * 1.0),
        inr=("inrange", "sum"), rz=("rz", "sum"),
        td=("td", "sum"), fga=("att", "sum"))
    gp = d.groupby([key, "season", "week"]).size() \
        .reset_index().groupby(key).size()
    g["games"] = g[key].map(gp)
    g["fga_g"] = g["fga"] / g["games"]
    g["inr_g"] = g["inr"] / g["games"]
    g["rz_g"] = g["rz"] / g["games"]
    g["rztd"] = g["td"] / g["rz"].clip(lower=1)
    g["conv"] = g["fga"] / g["inr"].clip(lower=1)
    return g

o = tbl("posteam", "offense", [2025, 2026])
o = o.sort_values("fga_g", ascending=False)
print("\n=== FG ATTEMPTS GENERATED (offense, 2025-26) ===")
print("%-5s %7s %9s %9s %8s %8s"
      % ("TEAM", "FGA/G", "INRANGE/G", "RZTRIP/G",
         "RZ TD%", "FGA/INR"))
for _, r in o.head(10).iterrows():
    print("%-5s %7.2f %9.2f %9.2f %7.1f%% %8.2f"
          % (r["posteam"], r["fga_g"], r["inr_g"],
             r["rz_g"], r["rztd"] * 100, r["conv"]))
print("   ...")
for _, r in o.tail(6).iterrows():
    print("%-5s %7.2f %9.2f %9.2f %7.1f%% %8.2f"
          % (r["posteam"], r["fga_g"], r["inr_g"],
             r["rz_g"], r["rztd"] * 100, r["conv"]))

d = tbl("defteam", "defense", [2025, 2026])
d = d.sort_values("fga_g")
print("\n=== FG ATTEMPTS ALLOWED (defense, 2025-26) ===")
print("%-5s %7s %9s %8s   %s"
      % ("TEAM", "FGA/G", "INRANGE/G", "RZ TD%", ""))
for _, r in d.head(6).iterrows():
    print("%-5s %7.2f %9.2f %7.1f%%   stingy"
          % (r["defteam"], r["fga_g"], r["inr_g"],
             r["rztd"] * 100))
print("   ...")
for _, r in d.tail(6).iterrows():
    print("%-5s %7.2f %9.2f %7.1f%%   generous"
          % (r["defteam"], r["fga_g"], r["inr_g"],
             r["rztd"] * 100))

OUT = {"off": {r["posteam"]: {
           "fga_g": round(r["fga_g"], 3),
           "inr_g": round(r["inr_g"], 3),
           "rztd": round(r["rztd"], 4),
           "conv": round(r["conv"], 4)}
        for _, r in o.iterrows()},
       "def": {r["defteam"]: {
           "fga_g": round(r["fga_g"], 3),
           "inr_g": round(r["inr_g"], 3),
           "rztd": round(r["rztd"], 4)}
        for _, r in d.iterrows()},
       "lg_fga": round(float(o["fga_g"].mean()), 3),
       "lg_inr": round(float(o["inr_g"].mean()), 3)}
json.dump(OUT, open("kickopp.json", "w"), indent=1)
print("\nleague avg: %.2f FG att/game, %.2f drives in range"
      % (OUT["lg_fga"], OUT["lg_inr"]))
print("wrote kickopp.json")

print("\n=== IS FG VOLUME STABLE YEAR TO YEAR? ===")
a = tbl("posteam", "", [2025])[["posteam", "fga_g"]]
b = tbl("posteam", "", [2026])[["posteam", "fga_g"]]
m = a.merge(b, on="posteam", suffixes=("_25", "_26"))
if len(m) > 10:
    print("  team FG attempts/gm, 2025 vs 2026:  r = %.3f"
          % np.corrcoef(m["fga_g_25"], m["fga_g_26"])[0, 1])
