import json
import numpy as np

N = 20000
rng = np.random.default_rng(11)
S = json.load(open("lgstate.json"))
C = json.load(open("lgcalc.json"))
CUR, SPOTS = S["cur"], S["spots"]
TEAMS = {int(k): v for k, v in S["teams"].items()}
RES = {int(k): v for k, v in S["results"].items()}
SCH = {int(k): v for k, v in S["sched"].items()}
PROJ = {int(k): {int(w): v for w, v in d.items()}
        for k, d in C["proj"].items()}

RID = sorted(TEAMS)
IX = {r: i for i, r in enumerate(RID)}
NT = len(RID)

# weekly volatility: each team's own scores, shrunk to the
# league's. five games is not enough to trust alone.
weekly = {r: [] for r in RID}
for w, games in RES.items():
    for g in games:
        weekly[g["a"]].append(g["ap"])
        weekly[g["b"]].append(g["bp"])
allsd = np.std([x for v in weekly.values() for x in v])
SD = np.zeros(NT)
for r in RID:
    v = weekly[r]
    own = np.std(v) if len(v) >= 3 else allsd
    SD[IX[r]] = 0.45 * own + 0.55 * allsd
print("league weekly sd %.1f" % allsd)

W0 = np.array([TEAMS[r]["w"] for r in RID], float)
P0 = np.array([TEAMS[r]["pf"] for r in RID], float)
wins = np.tile(W0, (N, 1))
pf = np.tile(P0, (N, 1))
ahead = [w for w in sorted(SCH) if w >= CUR]
print("simulating weeks %d-%d x %d seasons"
      % (ahead[0], ahead[-1], N))

for w in ahead:
    mu = np.array([PROJ[r].get(w, 110.0) for r in RID])
    sc = rng.normal(mu[None, :], SD[None, :], (N, NT))
    sc = np.maximum(sc, 30.0)
    pf += sc
    for a, b in SCH[w]:
        ia, ib = IX[a], IX[b]
        wa = sc[:, ia] > sc[:, ib]
        wins[:, ia] += wa
        wins[:, ib] += ~wa

key = wins * 1e6 + pf
rank = np.argsort(-key, axis=1)
seed = np.empty((N, NT), int)
rows = np.arange(N)[:, None]
seed[rows, rank] = np.arange(NT)[None, :]
made = seed < SPOTS

def duel(x, y):
    a = rng.normal(0, 1, N) + np.array(
        [PROJ[RID[i]].get(16, 110) for i in x]) / 10.0
    b = rng.normal(0, 1, N) + np.array(
        [PROJ[RID[i]].get(16, 110) for i in y]) / 10.0
    return np.where(a > b, x, y)

s = [rank[:, i] for i in range(SPOTS)]
champ = duel(duel(s[0], duel(s[3], s[4])),
             duel(s[1], duel(s[2], s[5])))
ttl = np.array([(champ == i).mean() for i in range(NT)])

OUT = []
for r in RID:
    i = IX[r]
    t = TEAMS[r]
    lk = C["luck"].get(str(r), {})
    OUT.append({
        "rid": r, "name": t["name"],
        "rec": "%d-%d" % (t["w"], t["l"]),
        "pf": round(t["pf"], 1),
        "luck": round(lk.get("luck", 0), 1),
        "allplay": lk.get("allplay", ""),
        "proj_w": round(float(wins[:, i].mean()), 1),
        "med_w": float(np.median(wins[:, i])),
        "w10": float(np.percentile(wins[:, i], 10)),
        "w90": float(np.percentile(wins[:, i], 90)),
        "po": float(made[:, i].mean()),
        "bye": float((seed[:, i] < 2).mean()),
        "title": float(ttl[i]),
        "last": float((seed[:, i] == NT - 1).mean()),
        "seed_pct": [round(float((seed[:, i] == k).mean()), 4)
                     for k in range(NT)],
        "ros": round(float(sum(PROJ[r].get(w, 0)
                               for w in ahead)), 1),
        "wk_now": PROJ[r].get(CUR, 0),
    })
OUT.sort(key=lambda x: -x["po"])
json.dump({"cur": CUR, "spots": SPOTS, "sims": N,
           "rows": OUT},
          open("site/_lgsim.json", "w"),
          separators=(",", ":"))

print("\n=== PROJECTED FINISH (from actual %d-%d records) ==="
      % (CUR - 1, 0))
print("%-24s %5s %6s %7s %7s %7s %7s"
      % ("TEAM", "REC", "LUCK", "PROJ W", "PLAYOFF",
         "TITLE", "LAST"))
for o in OUT:
    print("%-24s %5s %+6.1f %7.1f %6.1f%% %6.1f%% %6.1f%%"
          % (o["name"][:24], o["rec"], o["luck"],
             o["proj_w"], 100 * o["po"], 100 * o["title"],
             100 * o["last"]))

print("\n=== MOST LIKELY FINAL ORDER ===")
mo = sorted(OUT, key=lambda x: -x["proj_w"])
for i, o in enumerate(mo, 1):
    bar = "".join("#" if p > .18 else ("+" if p > .09 else ".")
                  for p in o["seed_pct"])
    print("  %2d %-24s %4.1f-%-4.1f  %s"
          % (i, o["name"][:24], o["proj_w"],
             (CUR - 1 + len(ahead)) - o["proj_w"], bar))
print("\n     (each bar = chance of finishing 1st..%dth)" % NT)
