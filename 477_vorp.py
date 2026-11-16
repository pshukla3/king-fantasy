import json

TEAMS = 10
SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
FLEX = 2
FLEXPOS = ("RB", "WR", "TE")

B = json.load(open("site/_board.json"))
rows = [r for r in B["rows"] if r.get("live") is not None]
rows.sort(key=lambda r: -(r["live"] or 0))

need = {p: n * TEAMS for p, n in SLOTS.items()}
flex_left = FLEX * TEAMS
started = {p: 0 for p in SLOTS}

for r in rows:
    p = r.get("pos")
    if p not in need:
        continue
    if started[p] < need[p]:
        started[p] += 1
        r["_st"] = 1
    elif p in FLEXPOS and flex_left > 0:
        flex_left -= 1
        started[p] += 1
        r["_st"] = 1

# replacement = best player at that position NOT starting
REP = {}
for r in rows:
    p = r.get("pos")
    if p in SLOTS and not r.get("_st") and p not in REP:
        REP[p] = r["live"] or 0.0
for p in SLOTS:
    REP.setdefault(p, 0.0)

print("=== REPLACEMENT LEVEL (10-tm, 1QB/2RB/2WR/1TE/2FLX) ===")
for p in ("QB", "RB", "WR", "TE", "K", "DEF"):
    print("   %-4s  started %3d   replacement %6.2f ppg"
          % (p, started.get(p, 0), REP[p]))

# Discount VORP by how PREDICTABLE the position is.
# Walk-forward over 4,481 kicker-games: our projection
# correlates with actual at r=0.061, and a kicker's own
# week predicts his next at r=0.04. A 1.5-point edge you
# cannot forecast is not worth 1.5 points. Kickers are
# round-15 picks and waiver churn -- rank them there.
STREAM = {"K": 0.08, "DEF": 0.25}
for r in B["rows"]:
    p = r.get("pos")
    lv = r.get("live")
    if p in REP and lv is not None:
        _v = max(0.0, lv - REP[p]) * STREAM.get(p, 1.0)
        r["vorp"] = round(_v, 2)
        r["uvorp"] = r["vorp"]
    r.pop("_st", None)
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("\nrecomputed VORP on one consistent scale")

t = sorted([r for r in B["rows"] if r.get("vorp")],
           key=lambda r: -r["vorp"])[:20]
print("\n=== TOP 20 BY VALUE OVER REPLACEMENT ===")
print("  %-3s %-22s %-4s %7s %7s"
      % ("#", "PLAYER", "POS", "PPG", "VORP"))
for i, r in enumerate(t, 1):
    print("  %-3d %-22s %-4s %7.1f %7.2f"
          % (i, r["n"][:22], r.get("pos"), r["live"], r["vorp"]))

q = [r for r in B["rows"] if r.get("pos") == "QB"
     and r.get("vorp")]
q.sort(key=lambda r: -r["vorp"])
print("\n=== QBs on the same scale ===")
for r in q[:6]:
    print("  %-22s %7.1f ppg   VORP %6.2f"
          % (r["n"][:22], r["live"], r["vorp"]))
