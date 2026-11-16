import json, re, math

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
SL = json.load(open("site/_slteams.json"))
ROWS = [r for r in B["rows"] if r.get("live") is not None]
NT = len(SL.get("teams", [])) or 10
SLOTS = [s for s in SL.get("slots", [])
         if s not in ("BN", "IR", "TAXI")]
EL = {"QB": ["QB"], "RB": ["RB"], "WR": ["WR"],
      "TE": ["TE"], "K": ["K"], "DEF": ["DEF", "DST"],
      "FLEX": ["RB", "WR", "TE"],
      "SUPER_FLEX": ["QB", "RB", "WR", "TE"]}
print("league: %d teams, slots %s" % (NT, SLOTS))

# --- measured replacement level -----------------------
pool = sorted(ROWS, key=lambda r: -r["live"])
used = set()
order = [s for s in SLOTS if "FLEX" not in s] * NT
order += [s for s in SLOTS if "FLEX" in s] * NT
for s in order:
    ok = EL.get(s, [])
    for r in pool:
        if id(r) in used:
            continue
        if r.get("pos") in ok:
            used.add(id(r))
            break

REPL, CREP = {}, {}
for pos in ("QB", "RB", "WR", "TE", "K", "DEF"):
    rest = [r for r in pool if id(r) not in used
            and (r.get("pos") == pos
                 or (pos == "DEF"
                     and r.get("pos") in ("DEF", "DST")))]
    REPL[pos] = rest[0]["live"] if rest else 0.0
    cs = [r.get("ceil") for r in rest[:5]
          if r.get("ceil") is not None]
    CREP[pos] = (sum(cs) / len(cs)) if cs else 0.0
    print("  replacement %-4s pts %6.2f  ceil %6.2f  (%s)"
          % (pos, REPL[pos], CREP[pos],
             rest[0]["n"] if rest else "-"))

WEEK, LAST = 2, 17
S = 3.2   # softness of the depth curve, in points
FLOOR = 1.0
STREAM = 0.30   # K and DEF are droppable weekly
CURVE = 1.35    # stars are worth more than linear:
                # you can only start ten players
SCALE = 10000.0  # every rosterable player keeps some
             # value: a bench body is still a bye
             # week fill and trade filler


def softplus(v, s=S):
    """Smooth max(0,v): a player 2 points below
    replacement keeps real but small value instead of
    collapsing to zero."""
    x = v / s
    if x > 30:
        return v
    return s * math.log1p(math.exp(x))


OUT = []
for r in ROWS:
    pos = r.get("pos")
    key = "DEF" if pos in ("DEF", "DST") else pos
    rep = REPL.get(key, 0.0)
    left = LAST - WEEK + 1
    bye = r.get("bye") or 0
    if bye and bye >= WEEK:
        left -= 1
    inj = str(r.get("inj") or "")
    if re.match(r"^(Out|IR|PUP|Sus)", inj):
        left = max(1, left - 4)
    elif re.match(r"^Doubt", inj):
        left = max(1, left - 1)

    vw = r["live"] - rep
    if key in ("K", "DEF"):
        vw *= STREAM

    start = softplus(vw)
    # upside: ceiling above a replacement ceiling is what
    # wins weeks you would otherwise lose
    ce = r.get("ceil")
    up = 0.0
    if ce is not None:
        up = 0.18 * max(0.0, ce - CREP.get(key, 0.0))
    raw = (start + up) * left
    OUT.append({
        "i": r.get("pid"), "n": r["n"], "p": pos,
        "t": r.get("tm"),
        "g": round(r["live"], 2),
        "rec": round(float(r.get("floor") or 0), 2),
        "rep": round(rep, 2),
        "vw": round(vw, 2),
        "up": round(up, 2),
        "wk": left,
        "raw": raw,
    })

mx = max(x["raw"] for x in OUT) or 1.0
for x in OUT:
    v = SCALE * ((x["raw"] / mx) ** CURVE)
    x["val"] = int(round(max(FLOOR, v)))
    del x["raw"]

OUT.sort(key=lambda x: -x["val"])
json.dump(OUT, open("site/_tc.json", "w"),
          separators=(",", ":"))
zero = sum(1 for x in OUT if x["val"] <= 0.0)
import csv
with open("trade_values.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["rank", "player", "pos", "team",
                "proj", "replacement", "vorp_wk",
                "upside", "weeks", "value"])
    for i, x in enumerate(OUT, 1):
        w.writerow([i, x["n"], x["p"], x["t"],
                    x["g"], x["rep"], x["vw"],
                    x["up"], x["wk"], x["val"]])
print("wrote trade_values.csv (all %d players)"
      % len(OUT))
print("\nwrote site/_tc.json (%d players, %d at zero)"
      % (len(OUT), zero))

print("\n=== top 15 ===")
print("  %-24s %-4s %6s %6s %6s %6s"
      % ("PLAYER", "POS", "PROJ", "VORP", "UPSIDE", "VALUE"))
for x in OUT[:15]:
    print("  %-24s %-4s %6.1f %6.1f %6.1f %6d"
          % (x["n"][:24], x["p"], x["g"], x["vw"],
             x["up"], x["val"]))

print("\n=== a depth player should no longer be zero ===")
for x in OUT[-6:]:
    print("  %-24s %-4s proj %5.1f vorp %6.1f value %6d"
          % (x["n"][:24], x["p"], x["g"], x["vw"], x["val"]))

print("\n=== YOUR OFFER ===")
by = {norm(x["n"]): x for x in OUT}
GIVE = ["Tee Higgins", "George Pickens", "Deebo Samuel",
        "Josh Downs"]
GET = ["Puka Nacua", "DJ Moore", "Jakobi Meyers"]


def show(names, lbl):
    tot = 0.0
    print("  %s:" % lbl)
    for n in names:
        k = norm(n)
        x = by.get(k)
        if not x:
            cand = [v for kk, v in by.items()
                    if kk.split()[-1] == k.split()[-1]]
            x = cand[0] if cand else None
        if not x:
            print("    %-24s NOT FOUND" % n)
            continue
        tot += x["val"]
        print("    %-24s %-4s proj %5.1f  value %6d"
              % (x["n"][:24], x["p"], x["g"], x["val"]))
    print("    %-24s %25.1f" % ("TOTAL", tot))
    return tot


a = show(GIVE, "You give")
b = show(GET, "You get")
print("\n  net %+.1f  ->  %s"
      % (b - a, "accept" if b - a > 3 else
         ("decline" if b - a < -3 else "too close to call")))
