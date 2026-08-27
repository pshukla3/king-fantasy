import pandas as pd, re

K_PPG, DST_PPG = 7.69, 7.0
SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "K", "DST"]
FLEXOK = ("RB", "WR", "TE")

ROSTER = [
    ("Caleb Williams",     "QB",  "CHI", 10),
    ("Omarion Hampton",    "RB",  "LAC",  7),
    ("Bhayshul Tuten",     "RB",  "JAX",  7),
    ("Jaxon Smith-Njigba", "WR",  "SEA", 11),
    ("George Pickens",     "WR",  "DAL", 14),
    ("Kyle Pitts",         "TE",  "ATL", 11),
    ("Tee Higgins",        "WR",  "CIN",  6),
    ("Josh Downs",         "WR",  "IND", 13),
    ("Harrison Butker",    "K",   "KC",   5),
    ("Seattle",            "DST", "SEA", 11),
    ("TreVeyon Henderson", "RB",  "NE",  11),
    ("Rico Dowdle",        "RB",  "PIT",  9),
    ("Keaton Mitchell",    "RB",  "LAC",  7),
    ("Deebo Samuel",       "WR",  "SF",   8),
    ("Rashid Shaheed",     "WR",  "SEA", 11),
]

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

B = pd.read_csv("board_final.csv", low_memory=False)
B["key"] = B["player_display_name"].map(norm)

def look(name, pos):
    n = norm(name)
    c = B[(B["key"] == n) & (B["position"] == pos)]
    if not len(c):
        c = B[B["key"].str.contains(n, na=False) & (B["position"] == pos)]
    return c.nlargest(1, "points").iloc[0] if len(c) else None

TEAM = []
for name, pos, tm, bye in ROSTER:
    if pos in ("K", "DST"):
        TEAM.append({"name": name, "pos": pos, "tm": tm, "bye": bye,
                     "ppg": K_PPG if pos == "K" else DST_PPG,
                     "g": 17.0, "src": "flat"})
        continue
    r = look(name, pos)
    if r is None:
        print("NO MATCH: %s (%s) -- set manually" % (name, pos))
        TEAM.append({"name": name, "pos": pos, "tm": tm, "bye": bye,
                     "ppg": 0.0, "g": 0.0, "src": "MISSING"})
    else:
        TEAM.append({"name": name, "pos": pos, "tm": tm, "bye": bye,
                     "ppg": float(r["points"]), "g": float(r["exp_games"]),
                     "src": "model"})

print("\n=== YOUR ROSTER, MODEL VIEW ===")
print("  pos  player                   tm  bye    ppg   expG  avail  season")
print("  " + "-" * 68)
for p in sorted(TEAM, key=lambda x: -x["ppg"]):
    print("  %-4s %-24s %-4s %2d  %5.1f  %5.1f  %4.0f%%  %5.0f"
          % (p["pos"], p["name"], p["tm"], p["bye"], p["ppg"], p["g"],
             100 * p["g"] / 17.0, p["ppg"] * p["g"]))

def best(pool, slot):
    c = ([p for p in pool if p["pos"] in FLEXOK] if slot == "FLEX"
         else [p for p in pool if p["pos"] == slot])
    return max(c, key=lambda x: x["ppg"]) if c else None

def week(w):
    pool = [p for p in TEAM if p["bye"] != w]
    used, out, holes = [], [], []
    for s in SLOTS:
        p = best([x for x in pool if x not in used], s)
        if p is None:
            holes.append(s)
        else:
            used.append(p)
        out.append((s, p))
    bench = [p for p in pool if p not in used]
    tot = adj = 0.0
    for s, p in out:
        if p is None:
            continue
        tot += p["ppg"]
        a = min(p["g"] / 17.0, 1.0)
        sub = best(bench, s)
        adj += a * p["ppg"] + (1 - a) * (sub["ppg"] if sub else 0.0)
    return tot, adj, holes

print("\n\n=== WEEK BY WEEK ===")
print("  healthy = everyone plays | adj = discounted by expected games\n")
print("  wk    healthy     adj   on bye                    gaps")
print("  " + "-" * 70)
sh = sa = 0.0
for w in range(1, 18):
    tot, adj, holes = week(w)
    sh += tot
    sa += adj
    byes = ", ".join(p["name"].split()[-1] for p in TEAM if p["bye"] == w)
    tag = "  <== NO " + "/".join(holes) if holes else ""
    print("  %2d%s  %7.1f %7.1f   %-24s%s"
          % (w, " *" if w >= 15 else "  ", tot, adj, byes[:24], tag))

print("\n  * = fantasy playoffs")
print("\n  SEASON   healthy %.0f   injury-adjusted %.0f   (%.1f pts/wk)"
      % (sh, sa, sa / 17))

print("\n\n=== BYE-WEEK LOAD ===")
cnt = {}
for p in TEAM:
    cnt.setdefault(p["bye"], []).append(p)
for w in sorted(cnt):
    pos = {}
    for p in cnt[w]:
        pos[p["pos"]] = pos.get(p["pos"], 0) + 1
    print("  wk %2d: %d out  (%s)"
          % (w, len(cnt[w]), " ".join("%d%s" % (v, k) for k, v in sorted(pos.items()))))
