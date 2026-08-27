import pandas as pd

TEAMS, ROUNDS = 10, 15
STARTERS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "DST", "K"]
FLEX_OK = {"FLEX": ["RB", "WR", "TE"]}
CAP = {"QB": 1, "TE": 2, "DST": 1, "K": 1, "RB": 7, "WR": 8}
LATE = {"DST": 13, "K": 14}
BENCH_W = 0.20

b = pd.read_csv("board_v7.csv", low_memory=False)
pool = b.head(430).to_dict("records")

def lineup(roster):
    av = sorted(roster, key=lambda r: -r["value"])
    used, tot = set(), 0.0
    for slot in STARTERS:
        ok = FLEX_OK.get(slot, [slot])
        for i, p in enumerate(av):
            if i not in used and p["position"] in ok:
                used.add(i); tot += max(0.0, p["value"]); break
    return tot

def eligible(p, cnt, rd, need_forced):
    pos = p["position"]
    if cnt.get(pos, 0) >= CAP.get(pos, 99):
        return False
    if pos in LATE and rd < LATE[pos]:
        return False
    if need_forced and pos not in need_forced:
        return False
    return True

rosters = {t: [] for t in range(1, TEAMS + 1)}
picks = []
for rd in range(1, ROUNDS + 1):
    order = range(1, TEAMS + 1) if rd % 2 else range(TEAMS, 0, -1)
    for slot, tm in enumerate(order, 1):
        cnt = {}
        for p in rosters[tm]:
            cnt[p["position"]] = cnt.get(p["position"], 0) + 1
        missing = [q for q in ("DST", "K") if cnt.get(q, 0) == 0]
        left = ROUNDS - rd + 1
        forced = missing if len(missing) >= left else None

        cur = lineup(rosters[tm])
        best, best_s = None, -1e18
        for i, p in enumerate(pool):
            if not eligible(p, cnt, rd, forced):
                continue
            gain = lineup(rosters[tm] + [p]) - cur
            s = gain + BENCH_W * max(0.0, p["value"]) - 0.05 * i
            if s > best_s:
                best_s, best = s, p
            if i > 80 and best is not None:
                break
        if best is None:
            for p in pool:
                if cnt.get(p["position"], 0) < CAP.get(p["position"], 99):
                    best = p; break
        pool.remove(best)
        rosters[tm].append(best)
        picks.append((rd, slot, tm, best))

print("=== MOCK v4 — 10tm PPR | QB/RB/RB/WR/WR/TE/FLEX/FLEX/DST/K + 5 bench ===")
for rd in range(1, ROUNDS + 1):
    print(f"\n--- Round {rd} ---")
    for r, s, tm, p in picks:
        if r == rd:
            a = f"{p['adp']:5.1f}" if p["adp"] == p["adp"] else "  -  "
            print(f"  {r}.{s:02d}  Team{tm:<3d} {p['player_display_name']:<22s} "
                  f"{p['position']:<4s} {p['team']:<4s} ppg={p['points']:5.1f} adp={a}")

print("\n\n=== TEAMS ===")
bad = 0
for tm in range(1, TEAMS + 1):
    r = rosters[tm]
    n = {}
    for p in r:
        n[p["position"]] = n.get(p["position"], 0) + 1
    ok = n.get("QB", 0) == 1 and n.get("DST", 0) == 1 and n.get("K", 0) == 1
    bad += 0 if ok else 1
    print(f"\n--- Team {tm}  starters={lineup(r):.0f}  "
          f"({n.get('QB',0)}QB {n.get('RB',0)}RB {n.get('WR',0)}WR {n.get('TE',0)}TE "
          f"{n.get('DST',0)}DST {n.get('K',0)}K){'' if ok else '   <-- INVALID'}")
    for p in sorted(r, key=lambda x: (x["position"], -x["value"])):
        print(f"  {p['position']:<4s} {p['player_display_name']:<24s} {p['team']:<4s} "
              f"{p['points']:5.1f} ppg x {p['exp_games']:4.1f}g")
print(f"\nrosters violating 1QB/1DST/1K: {bad}")
