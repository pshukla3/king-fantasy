import pandas as pd, re

DST_PPG = 7.69          # measured on real Sleeper keys, 2017-2025, r=0.265
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

MANUAL = {"Deebo Samuel": (10.0, 12.0)}
ROLEFIX = {"Bhayshul Tuten": 12.0}

def norm(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

B = pd.read_csv("board_final.csv", low_memory=False)
B["key"] = B["player_display_name"].map(norm)
KK = pd.read_csv("kicker_projections.csv")
KK["key"] = KK["kicker"].map(norm)

def kicker(name):
    last = norm(name.split()[-1])
    h = KK[KK["key"].str.contains(last, na=False)]
    return float(h.nlargest(1, "ppg")["ppg"].iloc[0]) if len(h) else 9.10

TEAM = []
for name, pos, tm, bye in ROSTER:
    if pos == "K":
        ppg, g, src = kicker(name), 17.0, "pbp"
    elif pos == "DST":
        ppg, g, src = DST_PPG, 17.0, "FLAT"
    elif name in MANUAL:
        ppg, g = MANUAL[name]
        src = "manual"
    else:
        n = norm(name)
        c = B[(B["key"] == n) & (B["position"] == pos)]
        if not len(c):
            c = B[B["key"].str.contains(n, na=False) & (B["position"] == pos)]
        if not len(c):
            print("NO MATCH: %s" % name)
            ppg, g, src = 0.0, 0.0, "MISSING"
        else:
            r = c.nlargest(1, "points").iloc[0]
            ppg, g, src = float(r["points"]), float(r["exp_games"]), "model"
    TEAM.append({"name": name, "pos": pos, "tm": tm, "bye": bye,
                 "ppg": ppg, "g": g, "src": src})

print("=== ROSTER ===")
print("  pos  player                   tm  bye    ppg   expG  src")
print("  " + "-" * 60)
for p in sorted(TEAM, key=lambda x: -x["ppg"]):
    print("  %-4s %-24s %-4s %2d  %5.1f  %5.1f  %s"
          % (p["pos"], p["name"], p["tm"], p["bye"], p["ppg"], p["g"], p["src"]))

def best(pool, slot):
    c = ([p for p in pool if p["pos"] in FLEXOK] if slot == "FLEX"
         else [p for p in pool if p["pos"] == slot])
    return max(c, key=lambda x: x["ppg"]) if c else None

def week(team, w):
    pool = [p for p in team if p["bye"] != w]
    used, out, holes = [], [], []
    for s in SLOTS:
        p = best([x for x in pool if x not in used], s)
        if p is None:
            holes.append(s)
        else:
            used.append(p)
        out.append((s, p))
    tot = adj = 0.0
    taken = list(used)
    for s, p in out:
        if p is None:
            continue
        tot += p["ppg"]
        a = min(p["g"] / 17.0, 1.0)
        sub = best([x for x in pool if x not in taken], s)
        if sub:
            taken.append(sub)
        adj += a * p["ppg"] + (1 - a) * (sub["ppg"] if sub else 0.0)
    return tot, adj, holes

def season(team, label):
    print("\n\n=== %s ===" % label)
    print("  wk    healthy     adj   on bye                    gaps")
    print("  " + "-" * 68)
    sh = sa = 0.0
    for w in range(1, 18):
        tot, adj, holes = week(team, w)
        sh += tot
        sa += adj
        byes = ", ".join(p["name"].split()[-1] for p in team if p["bye"] == w)
        tag = "  <== NO " + "/".join(holes) if holes else ""
        print("  %2d%s  %7.1f %7.1f   %-24s%s"
              % (w, " *" if w >= 15 else "  ", tot, adj, byes[:24], tag))
    print("\n  SEASON  healthy %.0f   adjusted %.0f   (%.1f/wk)" % (sh, sa, sa / 17))
    return sa

a = season(TEAM, "SCENARIO A: model as-is (real K, Deebo manual)")

T2 = [dict(p) for p in TEAM]
for p in T2:
    if p["name"] in ROLEFIX:
        p["ppg"] = ROLEFIX[p["name"]]
b = season(T2, "SCENARIO B: + depth-chart role correction (Tuten = JAX RB1)")

print("\n\n=== WHAT THE CORRECTIONS ARE WORTH ===")
print("  role correction (Tuten):  %+.0f pts over the season (%+.1f/wk)"
      % (b - a, (b - a) / 17))
print("  vs the 1882 you had before: %+.0f" % (b - 1882))
print("\n  SEA DST %.2f - measured, real league keys"
      % DST_PPG)
