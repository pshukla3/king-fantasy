import json
import nflreadpy as nfl

def g(r, k):
    v = r.get(k, 0)
    try:
        return float(v) if v == v else 0.0
    except Exception:
        return 0.0

def fp(r):
    return (g(r,"passing_yards")*.04 + g(r,"passing_tds")*4
            + g(r,"passing_interceptions")*-1
            + g(r,"rushing_yards")*.1 + g(r,"rushing_tds")*6
            + g(r,"receptions") + g(r,"receiving_yards")*.1
            + g(r,"receiving_tds")*6)

YR = [2022, 2023, 2024, 2025]
d = nfl.load_player_stats(YR).to_pandas()
d["fp"] = d.apply(fp, axis=1)
sc = nfl.load_schedules(YR).to_pandas()
hm = {}
for _, x in sc.iterrows():
    hm[(x["season"], x["week"], x["home_team"])] = 1
    hm[(x["season"], x["week"], x["away_team"])] = 0
d["hm"] = [hm.get((s, w, t)) for s, w, t
           in zip(d["season"], d["week"], d["team"])]
d = d[d["hm"].notna() & (d["fp"] > 0)]

OUT = {}
print("%-5s %8s %8s %8s %8s %8s"
      % ("POS", "HOME", "AWAY", "DIFF", "MULT", "N"))
for p in ("QB", "RB", "WR", "TE"):
    s = d[d["position"] == p]
    a = s[s["hm"] == 1]["fp"].mean()
    b = s[s["hm"] == 0]["fp"].mean()
    OUT[p] = round(a / b, 4)
    print("%-5s %8.2f %8.2f %+8.2f %8.3f %8d"
          % (p, a, b, a - b, a / b, len(s)))
json.dump(OUT, open("hfa.json", "w"), indent=1)
print("\nwrote hfa.json")
