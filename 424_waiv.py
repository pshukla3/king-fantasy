import json, re, ssl, certifi, os, datetime
import urllib.request as U
import nflreadpy as nfl

CTX = ssl.create_default_context(cafile=certifi.where())
HD = {"User-Agent": "Mozilla/5.0"}


def get(u):
    return json.loads(U.urlopen(
        U.Request(u, headers=HD), timeout=25,
        context=CTX).read())


def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


B = json.load(open("site/_board.json"))
ROWS = B.get("rows", [])
PM = json.load(open("site/_pmap.json"))
SL = json.load(open("site/_slteams.json"))
DR = {norm(r.get("n")): r for r in
      json.load(open("site/_dr.json"))}

BY_NAME = {norm(r.get("n")): r for r in ROWS}
BY_TEAM_DST = {str(r.get("tm")): r for r in ROWS
               if str(r.get("pos")) in ("DEF", "DST")}

# who is rostered anywhere in the league
ROST = {}
for t in SL.get("teams", []):
    for p in t.get("players", []):
        ROST[p.get("k") or norm(p.get("n"))] = t.get("owner")
print("rostered players: %d" % len(ROST))

# ---- season-to-date stats, 2026 ----
STAT = {}
try:
    d = nfl.load_player_stats(seasons=[2026]).to_pandas()
    c = set(d.columns)

    def g(r, *ns):
        for n in ns:
            if n in c:
                v = r.get(n)
                if v == v and v is not None:
                    return float(v)
        return 0.0

    for _, r in d.iterrows():
        pid = r.get("player_id")
        if not isinstance(pid, str):
            continue
        s = STAT.setdefault(pid, {
            "g": 0, "ratt": 0, "ryd": 0, "rtd": 0,
            "rec": 0, "tar": 0, "cyd": 0, "ctd": 0,
            "cmp": 0, "patt": 0, "pyd": 0, "ptd": 0,
            "int": 0})
        s["g"] += 1
        s["ratt"] += g(r, "carries", "rushing_attempts")
        s["ryd"] += g(r, "rushing_yards")
        s["rtd"] += g(r, "rushing_tds")
        s["rec"] += g(r, "receptions")
        s["tar"] += g(r, "targets")
        s["cyd"] += g(r, "receiving_yards")
        s["ctd"] += g(r, "receiving_tds")
        s["cmp"] += g(r, "completions")
        s["patt"] += g(r, "attempts", "passing_attempts")
        s["pyd"] += g(r, "passing_yards")
        s["ptd"] += g(r, "passing_tds")
        s["int"] += g(r, "passing_interceptions",
                      "interceptions")
    for k in STAT:
        for f in STAT[k]:
            STAT[k][f] = round(STAT[k][f], 1)
    print("season stats: %d players" % len(STAT))
except Exception as e:
    print("stats load failed: %s" % str(e)[:80])

# ---- trending ----
TR = {}
for kind in ("add", "drop"):
    try:
        t = get("https://api.sleeper.app/v1/players/nfl/"
                "trending/%s?lookback_hours=24&limit=60"
                % kind)
        for r in t:
            pid = str(r.get("player_id"))
            TR.setdefault(pid, {})[kind] = int(
                r.get("count") or 0)
        print("trending %s: %d" % (kind, len(t)))
    except Exception as e:
        print("trending %s failed: %s" % (kind, str(e)[:70]))

TREND = []
for pid, v in TR.items():
    m = PM.get(pid)
    if not m:
        continue
    nm = m.get("n")
    k = norm(nm)
    pos = m.get("p")
    b = (BY_TEAM_DST.get(pid) if pos in ("DEF", "DST")
         else BY_NAME.get(k))
    TREND.append({
        "pid": pid, "n": nm, "pos": pos, "tm": m.get("t"),
        "adds": v.get("add", 0), "drops": v.get("drop", 0),
        "img": (b or {}).get("img"),
        "proj": (b or {}).get("live"),
        "rk": (b or {}).get("rk"),
        "posrk": (b or {}).get("posrk"),
        "owner": ROST.get(k),
    })
TREND.sort(key=lambda x: -x["adds"])
print("trending joined: %d (%d with projections)"
      % (len(TREND), sum(1 for x in TREND if x["proj"])))

# ---- full player table ----
PLAYERS = []
for r in ROWS:
    k = norm(r.get("n"))
    gs = r.get("pid")
    dr = DR.get(k, {})
    PLAYERS.append({
        "n": r.get("n"), "pos": r.get("pos"),
        "tm": r.get("tm"), "img": r.get("img"),
        "gsis": gs, "rk": r.get("rk"),
        "posrk": r.get("posrk"), "bye": r.get("bye"),
        "inj": r.get("inj"),
        "proj": r.get("live"), "floor": r.get("floor"),
        "ceil": r.get("ceil"), "tier": r.get("tier"),
        "owner": ROST.get(k),
        "spts": dr.get("pts"), "savg": dr.get("avg"),
        "st": STAT.get(gs),
    })
print("player table: %d rows (%d free agents)"
      % (len(PLAYERS),
         sum(1 for p in PLAYERS if not p["owner"])))

OUT = {
    "gen": datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M"),
    "trend": TREND[:40],
    "players": PLAYERS,
}
json.dump(OUT, open("site/_waiv.json", "w"),
          separators=(",", ":"))
print("wrote site/_waiv.json (%d KB)"
      % (os.path.getsize("site/_waiv.json") // 1024))
print("\ntop 8 adds:")
for x in TREND[:8]:
    print("  %-22s %-4s %-4s adds %-9d proj %s  %s"
          % (x["n"][:22], x["pos"], x["tm"], x["adds"],
             x["proj"] if x["proj"] else "-",
             ("rostered: " + x["owner"]) if x["owner"]
             else "FREE"))
