import json
import nflreadpy as nfl

try:
    import fpts
    print("fpts module: found")
except Exception:
    fpts = None
    print("fpts module: NOT found, using inline full PPR")

FR = [(2025, "'25"), (2026, "'26")]
ALL = {}

for yr, tag in FR:
    try:
        d = nfl.load_player_stats(seasons=[yr])
        d = d.to_pandas()
    except Exception as e:
        print("%d: load failed %s" % (yr, str(e)[:70]))
        continue

    c = set(d.columns)

    def g(row, *names):
        for n in names:
            if n in c:
                v = row.get(n)
                if v == v and v is not None:
                    return float(v)
        return 0.0

    n = 0
    for _, r in d.iterrows():
        pid = r.get("player_id")
        if not isinstance(pid, str) or not pid:
            continue
        pts = (g(r, "passing_yards") * 0.04
               + g(r, "passing_tds") * 4
               + g(r, "passing_interceptions",
                   "interceptions") * -2
               + g(r, "rushing_yards") * 0.1
               + g(r, "rushing_tds") * 6
               + g(r, "receptions") * 1.0
               + g(r, "receiving_yards") * 0.1
               + g(r, "receiving_tds") * 6
               + (g(r, "rushing_fumbles_lost")
                  + g(r, "receiving_fumbles_lost")
                  + g(r, "sack_fumbles_lost")) * -2
               + (g(r, "passing_2pt_conversions")
                  + g(r, "rushing_2pt_conversions")
                  + g(r, "receiving_2pt_conversions")) * 2)
        wk = int(g(r, "week"))
        if wk <= 0:
            continue
        ALL.setdefault(pid, []).append(
            {"w": wk, "y": yr, "t": tag,
             "p": round(pts, 1)})
        n += 1
    print("%d: %d player-weeks" % (yr, n))

for pid in ALL:
    ALL[pid].sort(key=lambda x: (x["y"], x["w"]))
    ALL[pid] = ALL[pid][-24:]

json.dump(ALL, open("site/_hist.json", "w"),
          separators=(",", ":"))
import os
print("wrote site/_hist.json (%d players, %d KB)"
      % (len(ALL), os.path.getsize("site/_hist.json") // 1024))
k = list(ALL)[0]
print("sample %s: %s" % (k, json.dumps(ALL[k][-6:])))
