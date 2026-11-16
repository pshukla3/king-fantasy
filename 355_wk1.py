import json, re, os
import numpy as np
import pandas as pd
import fpts
from importlib import import_module
dst = import_module("349_dst")

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

WK = 1
ev = fpts.week_events(WK)
done = [e for e in ev if e["state"] == "post"]
print("week %d: %d of %d games final" % (WK, len(done),
                                         len(ev)))

ACT, DSTA = {}, {}
for e in done:
    s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
    for nm, v in fpts.score_summary(s).items():
        ACT[norm(nm)] = {"n": nm, "tm": v["tm"],
                         "p": v["p"]}
    for t, d in dst.dst_from_summary(s).items():
        DSTA[t.upper()] = d["pts"]
print("players scored %d | defenses %d"
      % (len(ACT), len(DSTA)))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["points"] = pd.to_numeric(B["points"], errors="coerce")
INJ = json.load(open("site/_inj.json"))
ZERO = {"out", "doubtful", "injured reserve",
        "suspension"}

rows = []
for _, r in B.iterrows():
    pos = str(r.get("position") or "")
    proj = float(r["points"]) if pd.notna(r["points"]) else None
    if proj is None:
        continue
    if pos == "DST":
        a = DSTA.get(str(r.get("team") or "").upper())
        if a is None:
            continue
        act = a
    else:
        m = ACT.get(r["k"])
        if m is None:
            continue
        act = m["p"]
    st = (INJ.get(r["k"]) or {}).get("status", "")
    rows.append({"n": r["player_display_name"], "pos": pos,
                 "tm": str(r.get("team") or ""),
                 "proj": round(proj, 2),
                 "act": round(act, 2),
                 "err": round(act - proj, 2),
                 "inj": st})
print("graded %d players" % len(rows))

D = pd.DataFrame(rows)
healthy = D[~D["inj"].str.lower().isin(ZERO)]

def stats(d, lab):
    if not len(d):
        return
    mae = d["err"].abs().mean()
    bias = d["err"].mean()
    c = (np.corrcoef(d["proj"], d["act"])[0, 1]
         if len(d) > 2 else float("nan"))
    print("  %-22s n=%-4d MAE %5.2f  bias %+5.2f  r %.3f"
          % (lab, len(d), mae, bias, c))

print("\n=== ACCURACY ===")
stats(D, "all graded")
stats(healthy, "excluding Out/IR")
print("\nby position (healthy only):")
for p in ("QB", "RB", "WR", "TE", "K", "DST"):
    stats(healthy[healthy["pos"] == p], p)

print("\n=== BOOMS (beat projection most) ===")
print("%-24s %-4s %6s %6s %7s" % ("PLAYER", "POS",
                                  "PROJ", "ACT", "DIFF"))
for _, r in D.sort_values("err", ascending=False)\
        .head(12).iterrows():
    print("%-24s %-4s %6.1f %6.1f %+7.1f"
          % (r["n"][:24], r["pos"], r["proj"], r["act"],
             r["err"]))

print("\n=== BUSTS (missed projection most) ===")
print("%-24s %-4s %6s %6s %7s %s"
      % ("PLAYER", "POS", "PROJ", "ACT", "DIFF", "STATUS"))
for _, r in D.sort_values("err").head(12).iterrows():
    print("%-24s %-4s %6.1f %6.1f %+7.1f %s"
          % (r["n"][:24], r["pos"], r["proj"], r["act"],
             r["err"], r["inj"]))

out = {"week": WK, "games": len(done), "n": len(rows),
       "mae": round(float(D["err"].abs().mean()), 2),
       "bias": round(float(D["err"].mean()), 2),
       "mae_healthy": round(
           float(healthy["err"].abs().mean()), 2),
       "n_healthy": int(len(healthy)),
       "rows": sorted(rows, key=lambda x: -x["act"]),
       "booms": sorted(rows, key=lambda x: -x["err"])[:15],
       "busts": sorted(rows, key=lambda x: x["err"])[:15]}
json.dump(out, open("site/_wk1.json", "w"))
print("\nwrote site/_wk1.json")
