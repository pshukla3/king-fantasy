import pandas as pd, random
from collections import defaultdict

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
BOARD = b.to_dict("records")

TEAMS, ROUNDS, ME = 10, 15, 7
NSIMS = 200
SIGMA = 2.5
RB_BUMP = 0

MIN = {"RB": 2, "WR": 2, "TE": 1, "QB": 1, "DST": 1, "K": 1}
CAP = {"QB": 1, "TE": 2, "DST": 1, "K": 1, "RB": 6, "WR": 7}
LATE = {"DST": 11, "K": 12}

SEQ = []
for rd in range(1, ROUNDS + 1):
    o = range(1, TEAMS + 1) if rd % 2 else range(TEAMS, 0, -1)
    for tm in o:
        SEQ.append((rd, tm))
MYPICKS = [i for i, (rd, tm) in enumerate(SEQ) if tm == ME]

def eligible(pool, cnt, rd, left):
    need = [q for q, m in MIN.items() if cnt.get(q, 0) < m]
    forced = need if len(need) >= left else None
    out = []
    for p in pool:
        pos = p["position"]
        if cnt.get(pos, 0) >= CAP.get(pos, 99):
            continue
        if pos in LATE and rd < LATE[pos] and not (forced and pos in forced):
            continue
        if forced and pos not in forced:
            continue
        out.append(p)
    if not out:
        out = [p for p in pool
               if cnt.get(p["position"], 0) < CAP.get(p["position"], 99)]
    if RB_BUMP:
        out.sort(key=lambda p: p["ecr"] - (RB_BUMP if p["position"] == "RB" else 0))
    return out

def one_sim(seed, avail, gone, sample):
    random.seed(seed)
    pool = list(BOARD)
    cnt = {t: {} for t in range(1, TEAMS + 1)}
    for i, (rd, tm) in enumerate(SEQ):
        if tm == ME:
            for p in pool[:20]:
                avail[i][p["player"]] += 1
            for p in BOARD:
                if p not in pool:
                    gone[i][p["position"]] += 1
        el = eligible(pool, cnt[tm], rd, ROUNDS - rd + 1)
        if tm == ME or len(el) == 1:
            p = el[0]
        else:
            p = el[min(int(abs(random.gauss(0, SIGMA))), len(el) - 1)]
        pool.remove(p)
        cnt[tm][p["position"]] = cnt[tm].get(p["position"], 0) + 1
        if sample is not None and tm == ME:
            sample.append((rd, i + 1, p))

avail = defaultdict(lambda: defaultdict(int))
gone = defaultdict(lambda: defaultdict(int))
sample = []
print("running %d sims..." % NSIMS)
for s in range(NSIMS):
    one_sim(s, avail, gone, sample if s == 0 else None)

INFO = {p["player"]: p for p in BOARD}
print("\n%s" % ("=" * 70))
print("SLOT %d  |  who actually reaches you  (%d sims, sigma=%.1f)"
      % (ME, NSIMS, SIGMA))
print("=" * 70)

for i in MYPICKS[:8]:
    rd = SEQ[i][0]
    g = gone[i]
    shape = "  ".join("%.1f %s" % (g[k] / NSIMS, k)
                      for k in ["RB", "WR", "TE", "QB"] if g[k])
    print("\n--- PICK %d  (round %d) ---" % (i + 1, rd))
    print("    off the board before you: %s" % (shape or "nobody"))
    rows = sorted(avail[i].items(), key=lambda kv: -kv[1])
    shown = 0
    for name, c in rows:
        pct = 100.0 * c / NSIMS
        if pct < 15 or shown >= 9:
            continue
        p = INFO[name]
        tag = "LOCK " if pct >= 90 else ("     " if pct >= 50 else "coin ")
        print("      %s%-22s %-3s ECR %3d   %3.0f%%"
              % (tag, name, p["position"], p["ecr"], pct))
        shown += 1

print("\n\n%s" % ("=" * 70))
print("ONE SAMPLE DRAFT FROM SLOT %d" % ME)
print("=" * 70)
c = {}
for rd, ov, p in sample:
    c[p["position"]] = c.get(p["position"], 0) + 1
    print("  R%-3d (#%3d)  %-24s %-4s %-4s ECR %d"
          % (rd, ov, p["player"], p["position"], p["team"], p["ecr"]))
print("\n  shape: %s" % " ".join("%d%s" % (v, k) for k, v in sorted(c.items())))
