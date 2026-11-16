import numpy as np, json
import nflreadpy as nfl

d = nfl.load_player_stats(seasons=[2025, 2026]).to_pandas()
oc = "opponent_team"
if oc not in d.columns:
    print("no opponent column: %s" % list(d.columns)[:25])
    raise SystemExit
d["tgt"] = d.get("targets", 0); d["rec"] = d.get("receptions", 0)
d["ryd"] = d.get("receiving_yards", 0)
d["rtd"] = d.get("receiving_tds", 0)
d["car"] = d.get("carries", 0)
d["rush"] = d.get("rushing_yards", 0)

g = (d.groupby([oc, "season", "week"])
     .agg(att=("tgt", "sum"), rec=("rec", "sum"),
          ryd=("ryd", "sum"), rtd=("rtd", "sum"),
          car=("car", "sum"), rush=("rush", "sum"))
     .reset_index())

L = {"att": g["att"].mean(),
     "ypc": g["ryd"].sum() / max(g["rec"].sum(), 1),
     "cr": g["rec"].sum() / max(g["att"].sum(), 1),
     "tdr": g["rtd"].sum() / max(g["att"].sum(), 1),
     "rypc": g["rush"].sum() / max(g["car"].sum(), 1)}
print("league baselines: %s"
      % {k: round(v, 3) for k, v in L.items()})

K = 6.0   # shrink each defense toward league by ~6 games
OUT = {}
for t, s in g.groupby(oc):
    n = len(s)
    w = n / (n + K)
    ypc = s["ryd"].sum() / max(s["rec"].sum(), 1)
    cr = s["rec"].sum() / max(s["att"].sum(), 1)
    tdr = s["rtd"].sum() / max(s["att"].sum(), 1)
    rypc = s["rush"].sum() / max(s["car"].sum(), 1)
    OUT[t] = {
        "n": int(n),
        "att": round(w * s["att"].mean() / L["att"]
                     + (1 - w), 3),
        "ypc": round(w * ypc / L["ypc"] + (1 - w), 3),
        "cr": round(w * cr / L["cr"] + (1 - w), 3),
        "tdr": round(w * tdr / L["tdr"] + (1 - w), 3),
        "rypc": round(w * rypc / L["rypc"] + (1 - w), 3),
    }

json.dump({"league": L, "def": OUT},
          open("site/_defadj.json", "w"),
          separators=(",", ":"))
print("\ntoughest pass defenses (yards per catch allowed):")
for t, v in sorted(OUT.items(), key=lambda x: x[1]["ypc"])[:8]:
    print("  %-5s ypc %.3f  catch %.3f  td %.3f  att %.3f"
          % (t, v["ypc"], v["cr"], v["tdr"], v["att"]))
print("\nsoftest:")
for t, v in sorted(OUT.items(),
                   key=lambda x: -x[1]["ypc"])[:8]:
    print("  %-5s ypc %.3f  catch %.3f  td %.3f  att %.3f"
          % (t, v["ypc"], v["cr"], v["tdr"], v["att"]))
print("\nspread in ypc allowed: %.3f to %.3f"
      % (min(v["ypc"] for v in OUT.values()),
         max(v["ypc"] for v in OUT.values())))
print("wrote site/_defadj.json (%d defenses)" % len(OUT))
