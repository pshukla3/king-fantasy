import pandas as pd

TEAMS, ROUNDS = 10, 15
STARTERS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"]
FLEX_OK = {"FLEX": ["RB", "WR", "TE"]}
NSTART = {p: STARTERS.count(p) for p in ["QB", "RB", "WR", "TE"]}
FLEXN = STARTERS.count("FLEX")
CAP = {"QB": NSTART["QB"], "TE": NSTART["TE"] + 1,
       "RB": NSTART["RB"] + FLEXN + 3, "WR": NSTART["WR"] + FLEXN + 3}
BENCH_W = 0.20

b = pd.read_csv("board_v6.csv", low_memory=False)
b["draft_val"] = -b["blend"]
pool = b.head(400).to_dict("records")

def lineup(roster):
    av = sorted(roster, key=lambda r: -r["value"])
    used, tot = set(), 0.0
    for slot in STARTERS:
        ok = FLEX_OK.get(slot, [slot])
        for i, p in enumerate(av):
            if i not in used and p["position"] in ok:
                used.add(i); tot += max(0.0, p["value"]); break
    return tot

rosters = {t: [] for t in range(1, TEAMS + 1)}
picks = []
for rd in range(1, ROUNDS + 1):
    order = range(1, TEAMS + 1) if rd % 2 else range(TEAMS, 0, -1)
    for slot, tm in enumerate(order, 1):
        cur = lineup(rosters[tm])
        cnt = {}
        for p in rosters[tm]:
            cnt[p["position"]] = cnt.get(p["position"], 0) + 1
        best, best_s = None, -1e18
        for i, p in enumerate(pool[:60]):
            if cnt.get(p["position"], 0) >= CAP.get(p["position"], 99):
                continue
            gain = lineup(rosters[tm] + [p]) - cur
            s = gain + BENCH_W * max(0.0, p["value"]) - 0.02 * i
            if s > best_s:
                best_s, best = s, p
        if best is None:
            best = pool[0]
        pool.remove(best)
        rosters[tm].append(best)
        picks.append((rd, slot, tm, best))

print("=== MOCK v3 — 10tm PPR, QB/RB/RB/WR/WR/TE/FLEX/FLEX (blended board) ===")
for rd in range(1, ROUNDS + 1):
    print(f"\n--- Round {rd} ---")
    for r, s, tm, p in picks:
        if r == rd:
            a = f"{p['adp']:5.1f}" if p["adp"] == p["adp"] else "  -  "
            print(f"  {r}.{s:02d}  Team{tm:<3d} {p['player_display_name']:<22s} "
                  f"{p['position']:<3s} {p['team']:<4s} ppg={p['points']:5.1f} "
                  f"g={p['exp_games']:4.1f} adp={a}")

print("\n\n=== TEAMS ===")
for tm in range(1, TEAMS + 1):
    r = rosters[tm]
    n = {}
    for p in r:
        n[p["position"]] = n.get(p["position"], 0) + 1
    print(f"\n--- Team {tm}   starters={lineup(r):.0f}   "
          f"({n.get('QB',0)}QB {n.get('RB',0)}RB {n.get('WR',0)}WR {n.get('TE',0)}TE) ---")
    for p in sorted(r, key=lambda x: (x["position"], -x["value"])):
        print(f"  {p['position']:<3s} {p['player_display_name']:<24s} {p['team']:<4s} "
              f"{p['points']:5.1f} ppg x {p['exp_games']:4.1f}g")
