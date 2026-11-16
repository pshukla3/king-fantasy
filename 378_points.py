import json, re
import fpts
from importlib import import_module
import pandas as pd
dst = import_module("349_dst")

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
POS = {}
IMG = {}
for _, r in B.iterrows():
    POS[r["k"]] = (str(r["position"]),
                   str(r.get("team") or ""))
    IMG[r["k"]] = str(r.get("img") or "")
DSTN = {str(r["team"]).upper(): r["player_display_name"]
        for _, r in B[B["position"] == "DST"].iterrows()}

TOT, GP = {}, {}
WK = fpts.nflweek()
for w in range(1, WK + 1):
    for e in fpts.week_events(w):
        if e["state"] != "post":
            continue
        s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
        for nm, v in fpts.score_summary(s).items():
            k = norm(nm)
            TOT[k] = TOT.get(k, 0.0) + v["p"]
            GP[k] = GP.get(k, 0) + 1
        for t, d in dst.dst_from_summary(s).items():
            nm = DSTN.get(t.upper())
            if not nm:
                continue
            k = norm(nm)
            TOT[k] = TOT.get(k, 0.0) + d["pts"]
            GP[k] = GP.get(k, 0) + 1

rows = []
for k, v in TOT.items():
    p, tm = POS.get(k, ("", ""))
    if not p:
        continue
    n = GP.get(k, 1)
    rows.append({"n": B[B["k"] == k]
                 ["player_display_name"].iloc[0],
                 "pos": p, "tm": tm,
                 "pts": round(v, 2), "g": n,
                 "ppg": round(v / max(n, 1), 2),
                 "img": IMG.get(k, "")})
rows.sort(key=lambda x: -x["pts"])
for i, r in enumerate(rows, 1):
    r["rk"] = i
BY = {}
for r in rows:
    BY.setdefault(r["pos"], []).append(r)
for p in BY:
    for i, r in enumerate(BY[p], 1):
        r["posrk"] = i

json.dump({"week": WK, "rows": rows,
           "pos": sorted(BY)},
          open("site/_points.json", "w"))
print("wrote site/_points.json | %d players through "
      "week %d" % (len(rows), WK))
print("\n%-3s %-24s %-4s %7s %4s %7s"
      % ("#", "PLAYER", "POS", "PTS", "G", "PPG"))
for r in rows[:15]:
    print("%-3d %-24s %-4s %7.2f %4d %7.2f"
          % (r["rk"], r["n"][:24], r["pos"], r["pts"],
             r["g"], r["ppg"]))
for p in ("QB", "RB", "WR", "TE", "K", "DST"):
    z = BY.get(p, [])[:3]
    if not z:
        continue
    print("\n--- %s ---" % p)
    for r in z:
        print("  %-24s %6.2f (%d g)"
              % (r["n"][:24], r["pts"], r["g"]))
