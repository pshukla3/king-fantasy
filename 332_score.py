import json, ssl, certifi, os
import urllib.request as U
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
BASE = ("https://site.api.espn.com/apis/site/v2/"
        "sports/football/nfl/")

def g(u):
    r = U.Request(u, headers=H)
    return json.loads(U.urlopen(r, timeout=25,
                                context=CTX).read())

# Full PPR. Key names come from ESPN's own "keys" list.
PTS = {
    "passingYards": 0.04,
    "passingTouchdowns": 4.0,
    "interceptions": -2.0,
    "rushingYards": 0.1,
    "rushingTouchdowns": 6.0,
    "receptions": 1.0,
    "receivingYards": 0.1,
    "receivingTouchdowns": 6.0,
    "fumblesLost": -2.0,
}
CATS = ("passing", "rushing", "receiving", "fumbles")

def num(v):
    v = str(v).strip()
    if v in ("", "-", "--"):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0

def scoregame(ev):
    s = g(BASE + "summary?event=" + str(ev))
    out = {}
    for t in ((s.get("boxscore") or {}).get("players")
              or []):
        tm = (t.get("team") or {}).get("abbreviation", "")
        for c in (t.get("statistics") or []):
            cn = (c.get("name") or "").lower()
            if cn not in CATS:
                continue
            ks = c.get("keys") or []
            for a in (c.get("athletes") or []):
                ath = a.get("athlete") or {}
                nm = ath.get("displayName")
                if not nm:
                    continue
                st = a.get("stats") or []
                r = out.setdefault(nm, {"tm": tm, "p": 0.0,
                                        "ln": []})
                for k, v in zip(ks, st):
                    if k in PTS:
                        d = num(v) * PTS[k]
                        if d:
                            r["p"] += d
                            r["ln"].append(
                                "%s %s" % (v, k[:14]))
    return out

sb = g(BASE + "scoreboard")
EV = [(e["id"], e.get("shortName", ""))
      for e in sb.get("events", [])
      if ((e.get("status") or {}).get("type")
          or {}).get("state") == "post"]
print("completed games: %d" % len(EV))
if not EV:
    raise SystemExit("nothing to score yet")

ACT = {}
for ev, sn in EV:
    r = scoregame(ev)
    print("  %-12s %3d players scored" % (sn, len(r)))
    ACT.update(r)

B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()]
PC = "points" if "points" in B.columns else "proj"
PR = {str(r["player_display_name"]).strip():
      float(r[PC] or 0)
      for _, r in B.iterrows()}

rows = []
for nm, r in ACT.items():
    if abs(r["p"]) < 0.01:
        continue
    pj = PR.get(nm)
    rows.append({"name": nm, "tm": r["tm"],
                 "act": round(r["p"], 2),
                 "proj": (round(pj, 2) if pj is not None
                          else None),
                 "why": ", ".join(r["ln"][:5])})
rows.sort(key=lambda x: -x["act"])

m = [r for r in rows if r["proj"] is not None]
print("\nscored %d players | %d matched to board"
      % (len(rows), len(m)))
if m:
    er = [abs(r["act"] - r["proj"]) for r in m]
    bi = [r["act"] - r["proj"] for r in m]
    print("MAE  %.2f pts" % (sum(er) / len(er)))
    print("BIAS %+.2f pts (neg = model too high)"
          % (sum(bi) / len(bi)))

print("\n%-22s %-4s %6s %6s %7s"
      % ("PLAYER", "TM", "ACT", "PROJ", "ERR"))
for r in rows[:22]:
    p = "%6.1f" % r["proj"] if r["proj"] is not None \
        else "    --"
    e = ("%+7.1f" % (r["act"] - r["proj"])
         if r["proj"] is not None else "      -")
    print("%-22s %-4s %6.1f %s %s"
          % (r["name"][:22], r["tm"], r["act"], p, e))

os.makedirs("site", exist_ok=True)
json.dump({"week": 1, "games": len(EV), "rows": rows},
          open("site/_acc_wk.json", "w"))
print("\nwrote site/_acc_wk.json (%d rows)" % len(rows))
