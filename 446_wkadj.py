import json, os, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())

def get(u):
    return json.loads(U.urlopen(
        U.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30, context=CTX).read())

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# Measured in 403_wk1adj.py: one week of results should
# move a season projection only a little.
SD = 8.34        # per-player weekly spread
WEIGHT = 0.33    # how much one game shifts our view
MAXFRAC = 0.12   # never move more than 12% of the number
MAXABS = 14.0    # or more than 14 points, whichever binds
CLIP = 2.0       # cap the surprise at 2 SDs

STORE = "wk_adjust.json"
ADJ = json.load(open(STORE)) if os.path.exists(STORE) else {}

SET = json.load(open("site/_scoring.json"))
PM = json.load(open("site/_pmap.json"))
PROJ = json.load(open("site/_wkproj.json"))
SKIP = {"pts_ppr", "pts_std", "pts_half_ppr", "gp",
        "gms_active", "tm_def_snp", "tm_off_snp",
        "tm_st_snp"}

def score(st):
    return sum(SET[k] * v for k, v in (st or {}).items()
               if k in SET and SET[k] and k not in SKIP)

def curweek():
    import datetime
    A = datetime.datetime(2026, 9, 8,
                          tzinfo=datetime.timezone.utc)
    d = datetime.datetime.now(datetime.timezone.utc) - A
    return max(1, min(18, d.days // 7 + 1))

CUR = curweek()
print("current week %d" % CUR)

# Week 1 is already baked into board_final.csv by
# 403_wk1adj.py -- applying it here would count the
# same game twice. Adjustments start at week 2.
BASELINE_THROUGH = 1
# only ingest COMPLETED weeks (CUR is in progress)
for wk in range(BASELINE_THROUGH + 1, CUR):
    key = str(wk)
    if key in ADJ:
        print("week %s already applied (%d players) "
              "- frozen" % (key, len(ADJ[key])))
        continue
    pj = PROJ.get(key)
    if not pj:
        print("week %s: no frozen projection, skipping" % key)
        continue
    try:
        ST = get("https://api.sleeper.app/v1/stats/nfl/"
                 "regular/2026/%s" % key)
    except Exception as e:
        print("week %s: stats failed %s" % (key, str(e)[:60]))
        continue

    moves = {}
    for pid, st in ST.items():
        if str(pid).startswith("TEAM_"):
            continue
        m = PM.get(str(pid)) or {}
        nm = m.get("n")
        if not nm:
            continue
        pos = m.get("p")
        k = m.get("t") if pos in ("DEF", "DST") else norm(nm)
        p = pj.get(k)
        if p is None or p <= 0:
            continue
        act = score(st)
        surprise = (act - p) / SD
        surprise = max(-CLIP, min(CLIP, surprise))
        raw = WEIGHT * surprise * SD
        cap = min(MAXFRAC * p, MAXABS)
        moves[k] = round(max(-cap, min(cap, raw)), 3)
    ADJ[key] = moves
    print("week %s: computed %d adjustments" % (key, len(moves)))

json.dump(ADJ, open(STORE, "w"), separators=(",", ":"))

TOT = {}
for wk, mv in ADJ.items():
    for k, v in mv.items():
        TOT[k] = TOT.get(k, 0.0) + v

B = json.load(open("site/_board.json"))
n = 0
for r in B.get("rows", []):
    pos = str(r.get("pos"))
    k = (str(r.get("tm")) if pos in ("DEF", "DST")
         else norm(r.get("n")))
    d = TOT.get(k)
    if d and r.get("live") is not None:
        r["live"] = round(max(0.0, r["live"] + d), 2)
        r["wkadj"] = round(d, 2)
        n += 1
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("\napplied cumulative adjustments to %d players" % n)

big = sorted(TOT.items(), key=lambda x: -abs(x[1]))[:14]
names = {}
for r in B["rows"]:
    pos = str(r.get("pos"))
    names[(str(r.get("tm")) if pos in ("DEF", "DST")
           else norm(r.get("n")))] = (r.get("n"),
                                      r.get("live"))
print("\nbiggest movers:")
for k, v in big:
    nm, lv = names.get(k, (k, None))
    print("  %-24s %+6.2f  -> now %s" % (str(nm)[:24], v, lv))
