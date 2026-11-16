import json, re, ssl, certifi
import urllib.request as U
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
LG = "1312181058833240064"
S = "https://api.sleeper.app/v1/"

def g(u, t=90):
    return json.loads(U.urlopen(U.Request(u, headers=H),
                      timeout=t, context=CTX).read())

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

lg = g(S + "league/" + LG)
SLOTS = lg.get("roster_positions") or []
print("league: %s | slots: %s" % (lg.get("name"), SLOTS))

R = g(S + "league/%s/rosters" % LG)
US = g(S + "league/%s/users" % LG)
UN = {u["user_id"]: (u.get("metadata", {}).get("team_name")
                     or u.get("display_name"))
      for u in US}
print("rosters %d | users %d" % (len(R), len(US)))

need = set()
for r in R:
    for p in (r.get("players") or []):
        need.add(str(p))
print("rostered ids: %d" % len(need))

print("fetching sleeper player index (~5MB, once)...")
P = g(S + "players/nfl", t=180)
print("player index: %d" % len(P))

B = pd.read_csv("board_final.csv")
# defenses join on team abbreviation, never on name:
# board says "Seahawks Defense", sleeper says
# "Seattle Seahawks"
ALT = {"LAR": "LA", "LA": "LAR", "WAS": "WSH",
       "WSH": "WAS", "JAX": "JAC", "JAC": "JAX",
       "ARI": "AZ", "AZ": "ARI"}
DSTP = {}
for _, r in B[B["position"] == "DST"].iterrows():
    t = str(r.get("team") or "").upper()
    v = r.get("proj_adj")
    if pd.isna(v):
        v = r.get("points")
    try:
        v = float(v)
    except (TypeError, ValueError):
        continue
    DSTP[t] = v
    if t in ALT:
        DSTP[ALT[t]] = v
print("DST projections keyed by team: %d" % len(DSTP))

KV = pd.to_numeric(B[B["position"] == "K"]["points"],
                   errors="coerce").dropna()
KFALL = float(KV.mean()) if len(KV) else 7.5
print("kicker fallback (mean of %d projected): %.2f"
      % (len(KV), KFALL))

PJ, ADJ = {}, {}
for _, r in B.iterrows():
    k = norm(r.get("player_display_name"))
    if not k:
        continue
    try:
        PJ[k] = float(r.get("points") or 0)
        ADJ[k] = float(r.get("proj_adj")
                       if pd.notna(r.get("proj_adj"))
                       else r.get("points") or 0)
    except (TypeError, ValueError):
        pass

def meta(pid):
    d = P.get(pid) or {}
    if not d and pid.isalpha():
        return {"n": pid + " Defense", "pos": "DEF",
                "tm": pid}
    nm = (d.get("full_name")
          or " ".join(filter(None, [d.get("first_name"),
                                    d.get("last_name")]))
          or pid)
    return {"n": nm,
            "pos": (d.get("position") or ""),
            "tm": (d.get("team") or ""),
            "inj": (d.get("injury_status") or "")}

teams = []
miss = 0
for r in R:
    ps = []
    for pid in (r.get("players") or []):
        pid = str(pid)
        m = meta(pid)
        k = norm(m["n"])
        if pid.isalpha():
            k = norm(m["n"].replace(" Defense", ""))
        est = False
        if pid.isalpha():
            pj = DSTP.get(pid.upper())
            if pj is None:
                pj = DSTP.get(ALT.get(pid.upper(), ""))
        else:
            pj = ADJ.get(k)
            if pj is None:
                pj = PJ.get(k)
        if pj is None and m["pos"] == "K":
            pj = KFALL
            est = True
        if pj is None:
            miss += 1
            pj = 0.0
        ps.append({"pid": pid, "n": m["n"], "k": k,
                   "pos": m["pos"], "tm": m["tm"],
                   "inj": m.get("inj", ""),
                   "ppg": round(float(pj), 2),
                   "est": est})
    ps.sort(key=lambda x: -x["ppg"])
    stg = r.get("settings") or {}
    fp = float(stg.get("fpts", 0)) + \
        float(stg.get("fpts_decimal", 0)) / 100.0
    fa = float(stg.get("fpts_against", 0)) + \
        float(stg.get("fpts_against_decimal", 0)) / 100.0
    teams.append({"id": r.get("roster_id"),
                  "owner": UN.get(r.get("owner_id"), ""),
                  "starters": [str(x) for x in
                               (r.get("starters") or [])],
                  "w": int(stg.get("wins", 0)),
                  "l": int(stg.get("losses", 0)),
                  "t": int(stg.get("ties", 0)),
                  "pf": round(fp, 2), "pa": round(fa, 2),
                  "players": ps})

# waiver pool: best board players nobody rosters
ROSTERED = set()
for t in teams:
    for p in t["players"]:
        ROSTERED.add(p["k"])
avail = []
for _, r in B.iterrows():
    k = norm(r.get("player_display_name"))
    if not k or k in ROSTERED:
        continue
    pos = str(r.get("position") or "")
    v = r.get("proj_adj")
    if pd.isna(v):
        v = r.get("points")
    try:
        v = float(v)
    except (TypeError, ValueError):
        continue
    if v <= 0:
        continue
    avail.append({"n": str(r.get("player_display_name")),
                  "pos": pos,
                  "tm": str(r.get("team") or ""),
                  "ppg": round(v, 2),
                  "inj": str(r.get("inj_status") or "")})
avail.sort(key=lambda x: -x["ppg"])
avail = avail[:120]
json.dump(avail, open("site/_avail.json", "w"))
print("wrote site/_avail.json | %d free agents "
      "(top: %s %.2f)"
      % (len(avail), avail[0]["n"] if avail else "-",
         avail[0]["ppg"] if avail else 0))

# schedule: every week's pairings from sleeper
sched = {}
for w in range(1, 19):
    try:
        M = g(S + "league/%s/matchups/%d" % (LG, w), t=30)
    except Exception:
        continue
    by = {}
    for m in M:
        mid = m.get("matchup_id")
        if mid is None:
            continue
        by.setdefault(str(mid), []).append(
            {"id": m.get("roster_id"),
             "pts": round(float(m.get("points") or 0), 2)})
    pair = [v for v in by.values() if len(v) == 2]
    if pair:
        sched[str(w)] = pair
json.dump(sched, open("site/_lgsched.json", "w"))
print("wrote site/_lgsched.json | %d weeks" % len(sched))

out = {"league": LG, "name": lg.get("name"),
       "slots": SLOTS, "teams": teams}
json.dump(out, open("site/_slteams.json", "w"))
print("\nwrote site/_slteams.json | %d teams, %d players, "
      "%d without a projection"
      % (len(teams), sum(len(t["players"]) for t in teams),
         miss))
for t in teams[:3]:
    print("  %-22s %2d players, %2d starters"
          % (t["owner"][:22], len(t["players"]),
             len(t["starters"])))
