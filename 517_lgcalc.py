import json, re, ssl, certifi
import urllib.request as U
import numpy as np

CTX = ssl.create_default_context(cafile=certifi.where())
S = json.load(open("lgstate.json"))
CUR, SPOTS = S["cur"], S["spots"]
TEAMS = {int(k): v for k, v in S["teams"].items()}
RES = {int(k): v for k, v in S["results"].items()}
SCH = {int(k): v for k, v in S["sched"].items()}

from namekey import nk as norm

print("pulling player map")
P = json.loads(U.urlopen(U.Request(
    "https://api.sleeper.app/v1/players/nfl",
    headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60, context=CTX).read())
PID = {}
for pid, p in P.items():
    if isinstance(p, dict) and p.get("full_name"):
        PID[pid] = {"n": p["full_name"],
                    "pos": p.get("position")}
    elif isinstance(p, dict) and p.get("position") == "DEF":
        PID[pid] = {"n": p.get("last_name") or pid,
                    "pos": "DEF"}

B = json.load(open("site/_board.json"))
BRD = {norm(r["n"]): r for r in B["rows"]}

# ---------- 1. LUCK: all-play record ----------
print("\n=== LUCK: actual vs all-play record ===")
allp = {r: [0, 0] for r in TEAMS}
for w, games in sorted(RES.items()):
    scores = []
    for g in games:
        scores += [(g["a"], g["ap"]), (g["b"], g["bp"])]
    for rid, pts in scores:
        beat = sum(1 for o, op in scores if o != rid and pts > op)
        allp[rid][0] += beat
        allp[rid][1] += len(scores) - 1 - beat
gp = len(RES)
print("  %-24s %6s %9s %8s %7s"
      % ("TEAM", "REC", "ALL-PLAY", "EXP W", "LUCK"))
LUCK = {}
for rid, t in sorted(TEAMS.items(),
                     key=lambda x: -x[1]["w"]):
    aw, al = allp[rid]
    exp = (aw / max(1, aw + al)) * gp
    luck = t["w"] - exp
    LUCK[rid] = {"exp_w": exp, "luck": luck,
                 "allplay": "%d-%d" % (aw, al)}
    print("  %-24s %3d-%-2d %9s %8.1f %+7.1f"
          % (t["name"][:24], t["w"], t["l"],
             "%d-%d" % (aw, al), exp, luck))

# ---------- 2. SCHEDULE FACED SO FAR ----------
print("\n=== SCHEDULE FACED (weeks 1-%d) ===" % gp)
opp_pts = {r: [] for r in TEAMS}
for w, games in sorted(RES.items()):
    for g in games:
        opp_pts[g["a"]].append(g["bp"])
        opp_pts[g["b"]].append(g["ap"])
rows = []
for rid, t in TEAMS.items():
    rows.append((np.mean(opp_pts[rid]) if opp_pts[rid] else 0,
                 t["name"], rid))
rows.sort(reverse=True)
for m, nm, rid in rows:
    print("  %-24s opp avg %6.1f  %s"
          % (nm[:24], m,
             "HARDEST" if m == rows[0][0] else
             ("easiest" if m == rows[-1][0] else "")))

# ---------- 3. WEEKLY ROSTER PROJECTIONS ----------
SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
FLEX = ("RB", "WR", "TE")

def wkproj(rid, week):
    pool = []
    for pid in TEAMS[rid]["players"]:
        meta = PID.get(pid)
        if not meta:
            continue
        r = BRD.get(norm(meta["n"]))
        if not r:
            continue
        v = None
        for x in (r.get("wk") or []):
            if x.get("w") == week:
                v = 0.0 if (x.get("o") == "BYE"
                            or x.get("out")) else x.get("m")
                break
        if v is None:
            v = (r.get("live") or 0) * 0.9
        pool.append((meta["pos"], float(v or 0)))
    pool.sort(key=lambda x: -x[1])
    used, tot = [], 0.0
    for slot in SLOTS:
        want = FLEX if slot == "FLEX" else (slot,)
        for i, (pos, v) in enumerate(pool):
            if i in used or pos not in want:
                continue
            used.append(i)
            tot += v
            break
    return tot

PROJ = {}
for rid in TEAMS:
    PROJ[rid] = {w: round(wkproj(rid, w), 1)
                 for w in sorted(SCH) if w >= CUR}
print("\n=== PROJECTED LINEUP, WEEK %d ===" % CUR)
for rid, t in sorted(TEAMS.items(),
                     key=lambda x: -PROJ[x[0]].get(CUR, 0)):
    nxt = [PROJ[rid].get(w, 0) for w in
           sorted(PROJ[rid])[:4]]
    print("  %-24s wk%d %6.1f   next: %s"
          % (t["name"][:24], CUR, PROJ[rid].get(CUR, 0),
             " ".join("%5.1f" % x for x in nxt[1:])))

json.dump({"luck": {str(k): v for k, v in LUCK.items()},
           "proj": {str(k): v for k, v in PROJ.items()},
           "oppfaced": {str(r): float(np.mean(opp_pts[r]))
                        if opp_pts[r] else 0.0 for r in TEAMS}},
          open("lgcalc.json", "w"), separators=(",", ":"))
print("\nwrote lgcalc.json")
