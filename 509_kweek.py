import json, re

BANDS = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
DEF = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
       "50_59": 5, "60_": 5}
try:
    MINE = json.load(open("league_scoring.json"))
except Exception:
    MINE = {}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

def score(x, S=None):
    if x.get("o") == "BYE" or x.get("out"):
        return 0.0
    t = 0.0
    for b in BANDS:
        if S:
            key = ("fgm_50p" if b in ("50_59", "60_")
                   else "fgm_" + b)
            pts = S.get(key)
            if pts is None:
                pts = S.get("fgm_" + b, 3)
            miss = S.get("fgmiss", -1)
            xw = S.get("xpm", 1)
        else:
            pts, miss, xw = DEF[b], -1, 1
        t += x["m_" + b] * pts
        t += (x["a_" + b] - x["m_" + b]) * miss
    t += x["xm"] * (MINE.get("xpm", 1) if S else 1)
    if S:
        t += (x["xa"] - x["xm"]) * S.get("xpmiss", 0)
    return round(t, 2)

K = json.load(open("site/_kproj.json"))
B = json.load(open("site/_board.json"))
PID = {norm(r["n"]): r.get("pid") for r in B["rows"]
       if r.get("pos") == "K"}

# _wkproj.json is the FROZEN weekly snapshot archive,
# keyed by week number -- never write player keys into it.
for f in ("site/_projweek.json",):
    try:
        J = json.load(open(f))
    except Exception as e:
        print("%s: %s - skipping" % (f, e))
        continue
    if not isinstance(J, dict):
        print("%s: not a dict - skipping" % f)
        continue
    n = 0
    for k, v in K.items():
        wk = []
        for x in v["wk"]:
            wk.append({"w": x["w"], "o": x.get("o"),
                       "h": x.get("h"),
                       "out": x.get("out", 0),
                       "m": score(x),
                       "ml": score(x, MINE) if MINE else score(x),
                       "lo": x.get("lo"), "hi": x.get("hi")})
        play = [y["m"] for y in wk
                if y["o"] != "BYE" and not y["out"]]
        rec = {"n": v["n"], "tm": v["tm"], "pos": "K",
               "pid": PID.get(k, ""),
               "ppg": round(sum(play) / len(play), 2)
               if play else 0.0,
               "wk": wk}
        J[k] = rec
        if rec["pid"]:
            J[rec["pid"]] = rec
        n += 1
    json.dump(J, open(f, "w"), separators=(",", ":"))
    print("%-24s +%d kickers (now %d entries)"
          % (f, n, len(J)))
