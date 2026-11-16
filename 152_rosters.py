import json
import re
import pandas as pd

L = pd.read_csv("league_rosters.csv")
bad = int(L["pid"].isna().sum())
print("rostered %d | unmatched %d" % (len(L), bad))
assert bad < len(L) * 0.1, (
    "player map still broken - run 149_playermap.py")

B = pd.read_csv("board_final.csv", low_memory=False)
BP = B.set_index("player_id")
SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
FLEXOK = ("RB", "WR", "TE")
ORD = {"QB": 0, "RB": 1, "WR": 2, "TE": 3,
       "K": 4, "DEF": 5}


def lineup(pool):
    used, tot, fill = set(), 0.0, []
    for s in SLOTS:
        ok = FLEXOK if s == "FLEX" else (s,)
        c = [(i, p) for i, p in enumerate(pool)
             if p["pos"] in ok and i not in used]
        if not c:
            fill.append((s, None))
            continue
        i, b = max(c, key=lambda x: x[1]["ppg"])
        used.add(i)
        tot += b["ppg"]
        fill.append((s, b))
    return tot, fill, used


OUT = []
for rid, g in L.groupby("roster_id"):
    pool = g.to_dict("records")
    tot, fill, used = lineup(pool)
    OUT.append((float(tot), int(rid),
                g.iloc[0]["team_name"],
                g.iloc[0]["owner"], pool, fill, used))
OUT.sort(reverse=True)

for seed, (tot, rid, nm, ow, pool, fill, used) in \
        enumerate(OUT, 1):
    me = "   <<< YOU" if rid == 1 else ""
    print("\n" + "=" * 62)
    print(" %d. %s  (@%s)   %.2f proj ppg%s"
          % (seed, nm, ow, tot, me))
    print("=" * 62)
    for s, p in fill:
        if p is None:
            print("  %-5s -- EMPTY --" % s)
        else:
            print("  %-5s %-24s %-4s %6.2f"
                  % (s, str(p["name"])[:24],
                     str(p["nfl"]), p["ppg"]))
    bench = [p for i, p in enumerate(pool)
             if i not in used]
    bench.sort(key=lambda x: -x["ppg"])
    if bench:
        print("  --- bench ---")
        for p in bench:
            print("  %-5s %-24s %-4s %6.2f"
                  % ("BN", str(p["name"])[:24],
                     str(p["nfl"]), p["ppg"]))

print("\n" + "=" * 62)
print(" POSITIONAL STRENGTH, ALL TEAMS")
print("=" * 62)
print("  %-22s %6s %6s %6s %6s %6s"
      % ("team", "QB", "RB", "WR", "TE", "TOTAL"))
for tot, rid, nm, ow, pool, fill, used in OUT:
    v = {}
    for p in ["QB", "RB", "WR", "TE"]:
        d = sorted([x["ppg"] for x in pool
                    if x["pos"] == p], reverse=True)
        k = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}[p]
        v[p] = sum(d[:k])
    print("  %-22s %6.1f %6.1f %6.1f %6.1f %6.1f"
          % (str(nm)[:22], v["QB"], v["RB"],
             v["WR"], v["TE"], tot))

R = []
for tot, rid, nm, ow, pool, fill, used in OUT:
    R.append({"roster_id": rid, "name": nm, "owner": ow,
              "proj": round(tot, 2),
              "players": [{"name": p["name"],
                           "pos": p["pos"],
                           "nfl": p["nfl"],
                           "ppg": round(p["ppg"], 2),
                           "bye": int(p["bye"]),
                           "pid": (None
                                   if p.get("pid") != p.get("pid")
                                   else p.get("pid"))}
                          for p in sorted(
                              pool,
                              key=lambda x: (
                                  ORD.get(x["pos"], 9),
                                  -x["ppg"]))]})
D = json.load(open("league_data.json"))
D["rosters"] = R
json.dump(D, open("league_data.json", "w"), indent=1)
print("\nadded %d full rosters to league_data.json" % len(R))
