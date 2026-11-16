import os
import re
import pandas as pd

SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DST"]
FLEXOK = ("RB", "WR", "TE")
WEEKS = list(range(1, 15))

B = pd.read_csv("board_final.csv", low_memory=False)
B = B[B["player_display_name"].notna()].copy()
B["key"] = B["player_display_name"].map(
    lambda s: re.sub(r"[^a-z]", "", str(s).lower()))

if not os.path.exists("byes_2026.csv"):
    import nflreadpy as nfl
    S = nfl.load_schedules(seasons=[2026])
    S = S.to_pandas() if hasattr(S, "to_pandas") else S
    seen = {}
    for _, r in S.iterrows():
        w = int(r["week"])
        for c in ["home_team", "away_team"]:
            seen.setdefault(str(r[c]), set()).add(w)
    rows = []
    for t, ws in seen.items():
        m = [w for w in range(1, 19) if w not in ws]
        rows.append({"team": t, "bye": m[0] if m else 0})
    pd.DataFrame(rows).to_csv("byes_2026.csv", index=False)
    print("built byes_2026.csv")

BY = pd.read_csv("byes_2026.csv")
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
BY["team"] = BY["team"].astype(str).replace(FIX)
BYE = dict(zip(BY["team"], BY["bye"]))
print("board %d rows | byes for %d teams"
      % (len(B), len(BYE)))

def look(nm):
    k = re.sub(r"[^a-z]", "", str(nm).lower())
    if not k:
        return None
    h = B[B["key"] == k]
    if not len(h):
        h = B[B["key"].str.contains(k, na=False)]
    if not len(h):
        return None
    return h.sort_values("rank").iloc[0]

def mk(nm):
    r = look(nm)
    if r is None:
        print("  NOT ON BOARD: %s" % nm)
        return None
    pp = r["points"]
    eg = r["exp_games"]
    pp = float(pp) if pp == pp else 0.0
    eg = float(eg) if eg == eg else 0.0
    tm = str(r["team"])
    st = r["status"]
    return {"nm": str(r["player_display_name"]),
            "ps": str(r["position"]), "tm": tm,
            "ppg": pp, "eg": eg,
            "adj": pp * min(eg / 17.0, 1.0),
            "bye": int(BYE.get(tm, 0)),
            "st": "" if st != st else str(st),
            "rk": int(r["rank"])}

def lineup(pool, wk=None, key="adj"):
    av = [(i, p) for i, p in enumerate(pool)
          if p["bye"] != wk]
    used = set()
    tot = 0.0
    fill = []
    for s in SLOTS:
        ok = FLEXOK if s == "FLEX" else (s,)
        c = [(i, p) for i, p in av
             if p["ps"] in ok and i not in used]
        if not c:
            fill.append((s, None))
            continue
        i, b = max(c, key=lambda x: x[1][key])
        used.add(i)
        tot += b[key]
        fill.append((s, b))
    return tot, fill

def season(pool):
    t = 0.0
    holes = []
    for w in WEEKS:
        v, f = lineup(pool, w)
        t += v
        g = [s for s, p in f if p is None]
        if g:
            holes.append((w, g))
    return t / len(WEEKS), holes

if not os.path.exists("trade.csv"):
    open("trade.csv", "w").write(
        "side,player\ngive,Josh Downs\nget,Rome Odunze\n")
    print("created trade.csv - edit it and rerun")

T = pd.read_csv("trade.csv")
T["side"] = T["side"].astype(str).str.strip().str.lower()
GIVE = [str(x).strip() for x in T[T["side"] == "give"]["player"]]
GET = [str(x).strip() for x in T[T["side"] == "get"]["player"]]

R = pd.read_csv("my_roster.csv")
NOW = [x for x in (mk(n) for n in R["player"]) if x]
gv = [x for x in (mk(n) for n in GIVE) if x]
gt = [x for x in (mk(n) for n in GET) if x]
gk = set(p["nm"] for p in gv)
AFT = [p for p in NOW if p["nm"] not in gk] + gt

print("\n=== TRADE ===")
for tag, lst in (("OUT", gv), ("IN ", gt)):
    for p in lst:
        print("  %s  %-22s %-3s %-4s %5.1f ppg  "
              "%4.1f g  bye %-2d %s"
              % (tag, p["nm"], p["ps"], p["tm"], p["ppg"],
                 p["eg"], p["bye"], p["st"]))

a, ha = season(NOW)
b, hb = season(AFT)
print("\n=== STARTING LINEUP, POINTS PER WEEK ===")
print("  before  %6.2f" % a)
print("  after   %6.2f" % b)
print("  delta   %+6.2f   (%+.0f over 14 weeks)"
      % (b - a, (b - a) * 14))
print("\n  roster before %d | after %d" % (len(NOW), len(AFT)))
if len(AFT) != len(NOW):
    print("  UNEVEN - you must drop or add to get back to 15")

if hb:
    print("\n=== WEEKS YOU CANNOT FIELD A LINEUP ===")
    for w, g in hb:
        print("  wk %2d  no %s" % (w, "/".join(g)))
else:
    print("\n  every week fields a legal lineup")

print("\n=== WEEK BY WEEK ===")
print("  wk   before    after    delta   on bye")
for w in WEEKS:
    x, _ = lineup(NOW, w)
    y, _ = lineup(AFT, w)
    bn = [p["nm"].split()[-1] for p in AFT if p["bye"] == w]
    print("  %2d  %7.1f  %7.1f  %+6.1f   %s"
          % (w, x, y, y - x, ", ".join(bn)[:32]))

print("\n=== LINEUP AFTER THE TRADE, WEEK 1 ===")
_, f = lineup(AFT, 1)
for s, p in f:
    if p is None:
        print("  %-5s -- EMPTY --" % s)
    else:
        print("  %-5s %-22s %-4s %5.2f"
              % (s, p["nm"], p["tm"], p["adj"]))
