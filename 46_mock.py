import pandas as pd

TEAMS, ROUNDS = 10, 15
STARTERS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"]
FLEX_OK = {"FLEX": ["RB", "WR", "TE"]}
MAXPOS = {"QB": 2, "TE": 3, "RB": 7, "WR": 8}
BENCH_W = 0.25

b = pd.read_csv("board_v4.csv", low_memory=False)
pool = b.head(400).to_dict("records")

def lineup(roster):
    av = sorted(roster, key=lambda r: -r["season_pts"])
    used, tot = set(), 0.0
    for slot in STARTERS:
        ok = FLEX_OK.get(slot, [slot])
        for i, p in enumerate(av):
            if i not in used and p["position"] in ok:
                used.add(i); tot += p["season_pts"]; break
    return tot

rosters = {t: [] for t in range(1, TEAMS + 1)}
picks = []
for rd in range(1, ROUNDS + 1):
    order = range(1, TEAMS + 1) if rd % 2 else range(TEAMS, 0, -1)
    for slot, tm in enumerate(order, 1):
        cur = lineup(rosters[tm])
        counts = {}
        for p in rosters[tm]:
            counts[p["position"]] = counts.get(p["position"], 0) + 1
        best, best_s = None, -1e18
        for p in pool[:60]:
            if counts.get(p["position"], 0) >= MAXPOS.get(p["position"], 99):
                continue
            s = (lineup(rosters[tm] + [p]) - cur) + BENCH_W * p["season_pts"]
            if s > best_s:
                best_s, best = s, p
        if best is None:
            best = pool[0]
        pool.remove(best)
        rosters[tm].append(best)
        picks.append((rd, slot, tm, best))

print("=== MOCK DRAFT — 10 team, PPR, QB/RB/RB/WR/WR/TE/FLEX/FLEX ===")
for rd in range(1, ROUNDS + 1):
    print(f"\n--- Round {rd} ---")
    for r, s, tm, p in picks:
        if r == rd:
            print(f"  {r}.{s:02d}  Team{tm:<3d} {p['player_display_name']:<22s} "
                  f"{p['position']:<3s} {p['team']:<4s} pts/g={p['points']:5.1f} "
                  f"g={p['exp_games']:4.1f} val={p['value']:7.1f}")

print("\n\n=== TEAMS ===")
for tm in range(1, TEAMS + 1):
    r = rosters[tm]
    print(f"\n--- Team {tm}  (projected starting lineup: {lineup(r):.0f} pts) ---")
    for p in sorted(r, key=lambda x: (x["position"], -x["season_pts"])):
        print(f"  {p['position']:<3s} {p['player_display_name']:<24s} {p['team']:<4s} "
              f"{p['points']:5.1f} ppg x {p['exp_games']:4.1f}g")
