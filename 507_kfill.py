import json, re

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

# bye week = the week missing from his team's schedule
import nflreadpy as _nfl
_sc = _nfl.load_schedules([2026]).to_pandas()
_wk = {}
for _, _g in _sc.iterrows():
    for _t in (_g["home_team"], _g["away_team"]):
        _wk.setdefault(_t, set()).add(int(_g["week"]))
BYE = {}
for _t, _ws in _wk.items():
    for _i in range(1, 19):
        if _i not in _ws:
            BYE[_t] = _i
            break
print("bye weeks resolved for %d teams" % len(BYE))


# Sleeper and nflverse disagree on a few team codes.
TEAMFIX = {"LAR": "LA", "OAK": "LV", "SD": "LAC",
           "SL": "LA", "STL": "LA", "ARZ": "ARI",
           "BLT": "BAL", "CLV": "CLE", "HST": "HOU",
           "WSH": "WAS", "JAC": "JAX"}
def tfix(t):
    t = (t or "").upper()
    return TEAMFIX.get(t, t)

B = json.load(open("site/_board.json"))
K = json.load(open("site/_kproj.json"))
have = {norm(r.get("n")): r for r in B["rows"]
        if r.get("pos") == "K"}

try:
    ROST = {norm(k["n"]): k
            for k in json.load(open("kickers_roster.json"))}
except Exception:
    ROST = {}

add = 0
for key, v in K.items():
    if key in have:
        continue
    meta = ROST.get(key, {})
    B["rows"].append({
        "n": v["n"], "pos": "K", "tm": v["tm"],
        "pid": meta.get("gsis") or "",
        "img": (("https://sleepercdn.com/content/nfl/"
                 "players/%s.jpg" % meta["sid"])
                if meta.get("sid") else ""),
        "adp": None, "bye": BYE.get(v["tm"]),
        "live": None, "vorp": 0.0,
    })
    add += 1
# every other rostered NFL kicker: on a team but not
# the starter, so he does not kick -> projected zero
have2 = {norm(r.get("n")) for r in B["rows"]
         if r.get("pos") == "K"}
bench = 0
for key, meta in ROST.items():
    if key in have2 or key in K:
        continue
    if not meta.get("tm"):
        continue
    B["rows"].append({
        "n": meta.get("n"), "pos": "K", "tm": tfix(meta.get("tm")),
        "pid": meta.get("gsis") or "",
        "img": (("https://sleepercdn.com/content/nfl/"
                 "players/%s.jpg" % meta["sid"])
                if meta.get("sid") else ""),
        "adp": None, "bye": BYE.get(tfix(meta.get("tm"))),
        "live": 0.0, "live_lg": 0.0, "vorp": 0.0,
        "wk": [], "kbench": 1,
        "conf": "low",
        "conf_why": "not his team's starting kicker",
    })
    bench += 1

# repair EVERY kicker row, not just the ones we append --
# rows from the original pipeline carry bye=0 and no image,
# and the board is rebuilt from scratch each deploy.
fix_img = fix_bye = 0
for r in B["rows"]:
    if r.get("pos") != "K":
        continue
    m = ROST.get(norm(r.get("n")), {})
    if not r.get("img") and m.get("sid"):
        r["img"] = ("https://sleepercdn.com/content/nfl/"
                    "players/%s.jpg" % m["sid"])
        fix_img += 1
    if not r.get("bye") and tfix(r.get("tm")) in BYE:
        r["bye"] = BYE[tfix(r["tm"])]
        fix_bye += 1
    if r.get("adp") is None and m.get("srank"):
        r["adp"] = float(m["srank"])
    if not r.get("inj"):
        r["inj"] = m.get("inj") or m.get("status") or "Active"
print("repaired %d images, %d bye weeks" % (fix_img, fix_bye))

json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("added %d missing starter rows" % add)
print("added %d backup kickers at zero" % bench)
print("K rows now: %d"
      % sum(1 for r in B["rows"] if r.get("pos") == "K"))
