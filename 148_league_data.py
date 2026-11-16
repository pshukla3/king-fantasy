import json
import re
import ssl
import numpy as np
import pandas as pd
import urllib.request as U
import certifi

CTX = ssl.create_default_context(cafile=certifi.where())
LG = "1312181058833240064"


def get(u):
    with U.urlopen(u, context=CTX, timeout=60) as r:
        return json.loads(r.read().decode())


_SUF = re.compile(r"\b(jr|sr|ii|iii|iv)\b\.?",
                  re.I)
def key(s):
    s = _SUF.sub("", str(s))
    return re.sub(r"[^a-z]", "", s.lower())


B = pd.read_csv("board_final.csv", low_memory=False)
RK = pd.read_csv("rookie_qb_seasons.csv")
R5 = RK[RK["pick"] <= 5]
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
m = (B["player_display_name"].astype(str)
     .str.contains("Mendoza", na=False))
if m.sum():
    att, ypa = 30.3, float(R5["ypa"].mean())
    tdr = float(R5["tdr"].mean())
    ry = float(R5["ryd"].sum() / R5["g"].sum())
    rt = float(R5["rtd"].sum() / R5["g"].sum())
    p = (att * ypa * float(V["pass_yd"])
         + att * tdr * float(V["pass_td"])
         + att * 0.0211 * float(V["pass_int"])
         + ry * float(V["rush_yd"])
         + rt * float(V["rush_td"]))
    B.loc[m, "points"] = p
    B.loc[m, "depth_rank"] = 1
    B.loc[m, "team"] = "LV"
    print("Mendoza -> QB1 LV at %.2f ppg" % p)
    B.to_csv("board_final.csv", index=False)
else:
    print("Mendoza NOT on board")

PJ = json.load(open("sleeper_players.json"))
RS = get("https://api.sleeper.app/v1/league/%s/rosters" % LG)
US = get("https://api.sleeper.app/v1/league/%s/users" % LG)
LI = get("https://api.sleeper.app/v1/league/%s" % LG)
un, tn = {}, {}
for u in US:
    md = u.get("metadata") or {}
    un[u["user_id"]] = u.get("display_name", "?")
    tn[u["user_id"]] = md.get("team_name") or u.get(
        "display_name", "?")

B["k"] = B["player_display_name"].apply(key)
DEFMAP = {}
for _, _r in B[B["position"].astype(str)
        .isin(["DEF", "DST"])].iterrows():
    _t = str(_r["team"]).upper()
    if _t and _t != "NAN":
        DEFMAP.setdefault(_t, _r)
_AL = {"LA": "LAR", "LAR": "LA",
       "WAS": "WSH", "WSH": "WAS",
       "ARI": "AZ", "AZ": "ARI",
       "JAX": "JAC", "JAC": "JAX"}
for _a, _b in list(_AL.items()):
    if _a in DEFMAP and _b not in DEFMAP:
        DEFMAP[_b] = DEFMAP[_a]
BK = {}
for _, r in B.sort_values("rank").iterrows():
    BK.setdefault(r["k"], r)
rows, miss = [], 0
for r in RS:
    for pid in (r.get("players") or []):
        d = PJ.get(str(pid), {})
        nm = d.get("full_name") or (
            str(d.get("first_name", "")) + " "
            + str(d.get("last_name", ""))).strip()
        b = BK.get(key(nm))
        if b is None and d.get("position") in\
                ("DEF", "DST"):
            b = DEFMAP.get(str(d.get("team",
                                      "")).upper())
        if b is None:
            miss += 1
        rows.append({
            "roster_id": r["roster_id"],
            "owner": un.get(r.get("owner_id"), "?"),
            "team_name": tn.get(r.get("owner_id"), "?"),
            "name": nm, "pos": d.get("position"),
            "nfl": d.get("team"),
            "pid": None if b is None else b["player_id"],
            "ppg": 0.0 if b is None else float(b["points"]),
            "bye": 0 if b is None else int(
                b["bye"] if "bye" in b and b["bye"] == b["bye"]
                else 0)})
L = pd.DataFrame(rows)
L.to_csv("league_rosters.csv", index=False)
print("\nleague: %s | rostered %d | unmatched %d"
      % (LI.get("name", "?"), len(L), miss))
if miss:
    print("UNMATCHED:")
    for _, r in L[L["pid"].isna()].head(12).iterrows():
        print("  %-4s %-24s %s"
              % (r["pos"], str(r["name"])[:24], r["nfl"]))

BY = pd.read_csv("byes_2026.csv")
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
BY["team"] = BY["team"].astype(str).replace(FIX)
BYE = dict(zip(BY["team"], BY["bye"]))
L["bye"] = L["nfl"].astype(str).replace(FIX).map(
    BYE).fillna(0).astype(int)
SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE",
         "FLEX", "FLEX", "K", "DEF"]
FLEXOK = ("RB", "WR", "TE")


def lineup(pool, wk=None):
    av = [p for p in pool if wk is None or p["bye"] != wk]
    used, tot, fill = set(), 0.0, []
    for s in SLOTS:
        ok = FLEXOK if s == "FLEX" else (s,)
        c = [(i, p) for i, p in enumerate(av)
             if p["pos"] in ok and i not in used]
        if not c:
            fill.append((s, None))
            continue
        i, b = max(c, key=lambda x: x[1]["ppg"])
        used.add(i)
        tot += b["ppg"]
        fill.append((s, b))
    return tot, fill


POOL = {}
for rid, g in L.groupby("roster_id"):
    POOL[int(rid)] = g.to_dict("records")
TEAMS = []
for rid, g in L.groupby("roster_id"):
    t, f = lineup(POOL[int(rid)])
    TEAMS.append({
        "roster_id": int(rid),
        "name": g.iloc[0]["team_name"],
        "owner": g.iloc[0]["owner"],
        "proj": round(t, 2),
        "starters": [{"slot": s,
                      "name": (p or {}).get("name", "EMPTY"),
                      "pos": (p or {}).get("pos", ""),
                      "nfl": (p or {}).get("nfl", ""),
                      "ppg": round((p or {}).get("ppg", 0), 2)}
                     for s, p in f]})
TEAMS.sort(key=lambda x: -x["proj"])
for i, t in enumerate(TEAMS):
    t["seed"] = i + 1

WK = {}
for w in range(1, 15):
    try:
        M = get("https://api.sleeper.app/v1/league"
                "/%s/matchups/%d" % (LG, w))
    except Exception:
        M = []
    byid = {}
    for r in M:
        byid.setdefault(r.get("matchup_id"), []).append(
            int(r["roster_id"]))
    games = []
    for mid, rs in sorted(byid.items(),
                          key=lambda x: (x[0] is None, x[0])):
        if len(rs) != 2:
            continue
        a, b2 = rs[0], rs[1]
        pa = lineup(POOL.get(a, []), w)[0]
        pb = lineup(POOL.get(b2, []), w)[0]
        games.append({"a": a, "b": b2,
                      "pa": round(pa, 2), "pb": round(pb, 2)})
    WK[str(w)] = games
    print("  wk %2d  %d games" % (w, len(games)))
print("built %d weeks" % len(WK))

own = set(L["pid"].dropna().astype(str))
FA = B[~B["player_id"].astype(str).isin(own)].copy()
FA = FA[FA["position"].isin(
    ["QB", "RB", "WR", "TE", "K", "DEF", "DST"])]
FA["position"] = FA["position"].replace({"DST": "DEF"})
FA = FA[FA["points"].notna() & (FA["points"] > 0)]
REP = {}
for p in ["QB", "RB", "WR", "TE", "K", "DEF"]:
    d = B[B["position"].replace({"DST": "DEF"}) == p]
    d = d[d["points"].notna()].sort_values(
        "points", ascending=False)
    n = {"QB": 10, "RB": 30, "WR": 30, "TE": 10,
         "K": 10, "DEF": 10}[p]
    REP[p] = float(d.iloc[min(n, len(d) - 1)]["points"])
FA["vorp"] = FA.apply(
    lambda r: r["points"] - REP.get(r["position"], 0),
    axis=1)
mine = POOL.get(1, [])
base = lineup(mine)[0]


def fit(r):
    add = dict(pos=r["position"], ppg=float(r["points"]),
               name=r["player_display_name"], bye=0)
    return lineup(mine + [add])[0] - base


FA["fit"] = FA.apply(fit, axis=1)
FA = FA.sort_values(["fit", "vorp"], ascending=False)
WV = []
for _, r in FA.head(60).iterrows():
    WV.append({
        "name": str(r["player_display_name"]),
        "pos": r["position"], "nfl": str(r["team"]),
        "ppg": round(float(r["points"]), 2),
        "vorp": round(float(r["vorp"]), 2),
        "fit": round(float(r["fit"]), 2),
        "adp": (None if r["adp"] != r["adp"]
                else float(r["adp"])),
               "pid": str(r["player_id"])})
OUT = {"league": {"name": LI.get("name", "League"),
                  "teams": len(TEAMS), "season": "2026",
                  "scoring": "Full PPR"},
       "teams": TEAMS, "weeks": WK, "waivers": WV,
       "my_roster_id": 1,
       "my_base": round(base, 2)}
json.dump(OUT, open("league_data.json", "w"), indent=1)
print("\n=== PROJECTED STANDINGS ===")
for t in TEAMS:
    me = "  <-- YOU" if t["roster_id"] == 1 else ""
    print("  %2d  %-24s %7.2f%s"
          % (t["seed"], str(t["name"])[:24],
             t["proj"], me))
print("\n=== TOP WAIVER ADDS FOR YOUR TEAM ===")
print("  %-24s %-4s %6s %6s %6s"
      % ("player", "pos", "ppg", "vorp", "fit"))
for w in WV[:15]:
    print("  %-24s %-4s %6.2f %+6.2f %+6.2f"
          % (w["name"][:24], w["pos"], w["ppg"],
             w["vorp"], w["fit"]))
print("\nwrote league_data.json")
