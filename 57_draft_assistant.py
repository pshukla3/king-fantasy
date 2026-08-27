import pandas as pd, re

b = pd.read_csv("board_ecr.csv")

EXTRA = [(205, "Jake Bates", "K", "DET"), (206, "Evan McPherson", "K", "CIN"),
         (207, "Chase McLaughlin", "K", "TB"), (208, "Jason Myers", "K", "SEA"),
         (209, "Harrison Butker", "K", "KC"), (210, "Cairo Santos", "K", "CHI"),
         (211, "Tyler Loop", "K", "BAL"), (212, "Eddy Pineiro", "K", "SF"),
         (213, "Chris Boswell", "K", "PIT"), (214, "Jake Elliott", "K", "PHI"),
         (215, "Buffalo Bills", "DST", "BUF"), (216, "Green Bay Packers", "DST", "GB")]
b = pd.concat([b, pd.DataFrame(EXTRA, columns=["ecr", "player", "position", "team"])],
              ignore_index=True).sort_values("ecr").reset_index(drop=True)
b["pos_rank"] = b.groupby("position")["ecr"].rank(method="min").astype(int)

TEAMS, ROUNDS, ME = 10, 15, 7
MIN = {"RB": 2, "WR": 2, "TE": 1, "QB": 1, "DST": 1, "K": 1}
CAP_AI = {"QB": 1, "TE": 2, "DST": 1, "K": 1, "RB": 6, "WR": 7}
CAP_ME = {"QB": 2, "TE": 3, "DST": 1, "K": 1, "RB": 8, "WR": 8}
LATE = {"DST": 11, "K": 12}

pool = b.to_dict("records")
rosters = {t: [] for t in range(1, TEAMS + 1)}

seq = []
for rd in range(1, ROUNDS + 1):
    o = range(1, TEAMS + 1) if rd % 2 else range(TEAMS, 0, -1)
    for tm in o:
        seq.append((rd, tm))
my_picks = [i for i, (rd, tm) in enumerate(seq) if tm == ME]

def counts(tm):
    c = {}
    for p in rosters[tm]:
        c[p["position"]] = c.get(p["position"], 0) + 1
    return c

def ai_pick(tm, rd):
    c = counts(tm)
    left = ROUNDS - rd + 1
    need = [q for q, m in MIN.items() if c.get(q, 0) < m]
    forced = need if len(need) >= left else None
    for p in pool:
        pos = p["position"]
        if c.get(pos, 0) >= CAP_AI.get(pos, 99):
            continue
        if pos in LATE and rd < LATE[pos] and not (forced and pos in forced):
            continue
        if forced and pos not in forced:
            continue
        return p
    return next(p for p in pool
                if c.get(p["position"], 0) < CAP_AI.get(p["position"], 99))

def dropoff(gap):
    out = {}
    for pos in ["RB", "WR", "TE", "QB", "DST", "K"]:
        now = next((p for p in pool if p["position"] == pos), None)
        if not now:
            continue
        later = next((p for p in pool[gap:] if p["position"] == pos), None)
        drop = (later["ecr"] - now["ecr"]) if later else 99
        out[pos] = (now, later, drop)
    return out

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

def find(txt):
    n = norm(txt)
    if not n:
        return None
    hits = [p for p in pool if n in norm(p["player"])]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        print("  ambiguous:", ", ".join(h["player"] for h in hits[:6]))
    else:
        print("  not found / already drafted")
    return None

print("=== LIVE DRAFT — you are Team %d of %d, snake, PPR ===" % (ME, TEAMS))
print("your picks (overall): %s" % [i + 1 for i in my_picks])

for i, (rd, tm) in enumerate(seq):
    if tm != ME:
        p = ai_pick(tm, rd)
        pool.remove(p)
        rosters[tm].append(p)
        continue

    nxt = next((j for j in my_picks if j > i), None)
    gap = (nxt - i - 1) if nxt else 0
    c = counts(ME)
    left = ROUNDS - rd + 1
    need = [q for q, m in MIN.items() if c.get(q, 0) < m]

    print("\n" + "=" * 74)
    tail = "next pick: overall %d, %d go first" % (nxt + 1, gap) if nxt else "last pick"
    print("YOUR PICK - round %d, overall %d   (%s)" % (rd, i + 1, tail))
    have = " ".join("%d%s" % (v, k) for k, v in sorted(c.items()))
    print("roster: %s | need: %s | %d picks left"
          % (have or "empty", ", ".join(need) or "nothing", left))

    print("\n  BEST AVAILABLE")
    for p in pool[:14]:
        print("    ECR %3d  %-24s %s%-3d %s"
              % (p["ecr"], p["player"], p["position"], p["pos_rank"], p["team"]))

    d = dropoff(gap)
    print("\n  DROPOFF (what you lose by waiting %d picks)" % gap)
    for pos, (now, later, drop) in sorted(d.items(), key=lambda x: -x[1][2]):
        if c.get(pos, 0) >= CAP_ME.get(pos, 99):
            continue
        lt = "%s (ECR %d)" % (later["player"], later["ecr"]) if later else "nobody left"
        flag = ""
        if pos in need and drop >= 20:
            flag = "  <== URGENT"
        elif pos in need:
            flag = "  <-- needed"
        print("    %-4s now: %-22s ECR %3d | later: %-30s drop %3d%s"
              % (pos, now["player"], now["ecr"], lt, drop, flag))

    cand = [p for p in pool
            if c.get(p["position"], 0) < CAP_ME.get(p["position"], 99)
            and not (p["position"] in LATE and rd < LATE[p["position"]]
                     and len(need) < left)]
    forced = need if len(need) >= left else None
    if forced:
        cand = [p for p in cand if p["position"] in forced]
        print("\n  FORCED: %d picks left, still need %s" % (left, ", ".join(need)))
    urgent = [p for p in cand
              if p["position"] in need and d.get(p["position"], (0, 0, 0))[2] >= 20]
    rec = (urgent or cand)[0]
    print("\n  >>> RECOMMEND: %s (%s, %s, ECR %d)"
          % (rec["player"], rec["position"], rec["team"], rec["ecr"]))

    while True:
        raw = input("  your pick (name, or ENTER for the rec): ").strip()
        p = rec if raw == "" else find(raw)
        if p:
            break
    pool.remove(p)
    rosters[ME].append(p)
    print("  --> drafted %s (%s)" % (p["player"], p["position"]))

print("\n\n" + "=" * 74)
print("FINAL ROSTERS")
for tm in range(1, TEAMS + 1):
    r = sorted(rosters[tm], key=lambda x: x["ecr"])
    c = counts(tm)
    ok = (c.get("QB", 0) >= 1 and c.get("DST", 0) == 1 and c.get("K", 0) == 1
          and c.get("RB", 0) >= 2 and c.get("WR", 0) >= 2 and c.get("TE", 0) >= 1)
    tag = "  <-- YOU" if tm == ME else ("" if ok else "  <-- INVALID")
    avg = sum(p["ecr"] for p in r) / len(r)
    shape = " ".join("%d%s" % (v, k) for k, v in sorted(c.items()))
    print("\n--- Team %d  avg ECR %.1f  (%s)%s" % (tm, avg, shape, tag))
    for p in r:
        print("  %-4s %-24s %-4s ECR %d"
              % (p["position"], p["player"], p["team"], p["ecr"]))
