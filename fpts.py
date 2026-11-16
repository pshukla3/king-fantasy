"""Single source of truth for full-PPR scoring."""
import json, ssl, certifi
import urllib.request as U
from datetime import datetime, timezone, timedelta

CTX = ssl.create_default_context(cafile=certifi.where())
HDR = {"User-Agent": "curl/8.7.1"}
BASE = ("https://site.api.espn.com/apis/site/v2/"
        "sports/football/nfl/")

PTS = {
    "passingYards": 0.04, "passingTouchdowns": 4.0,
    "interceptions": -2.0,
    "rushingYards": 0.1, "rushingTouchdowns": 6.0,
    "receptions": 1.0, "receivingYards": 0.1,
    "receivingTouchdowns": 6.0, "fumblesLost": -2.0,
}
CATS = ("passing", "rushing", "receiving", "fumbles")
KCAT, KKEY = "kicking", "totalKickingPoints"

# Week 1 of 2026 opens Thu Sep 10; weeks roll over
# Tuesday 00:00 local, so anchor on Tue Sep 8.
ANCHOR = datetime(2026, 9, 8, tzinfo=timezone.utc)

def nflweek(now=None):
    now = now or datetime.now(timezone.utc)
    d = (now - ANCHOR).days
    if d < 0:
        return 1
    return min(18, d // 7 + 1)

def get(u):
    r = U.Request(u, headers=HDR)
    return json.loads(U.urlopen(r, timeout=25,
                                context=CTX).read())

def num(v):
    v = str(v).strip()
    if v in ("", "-", "--"):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0

def score_summary(s):
    """summary payload -> {name: {tm, pos, p}}"""
    out = {}
    for t in ((s.get("boxscore") or {}).get("players")
              or []):
        tm = (t.get("team") or {}).get("abbreviation", "")
        for c in (t.get("statistics") or []):
            cn = (c.get("name") or "").lower()
            ks = c.get("keys") or []
            if cn not in CATS and cn != KCAT:
                continue
            for a in (c.get("athletes") or []):
                ath = a.get("athlete") or {}
                nm = ath.get("displayName")
                if not nm:
                    continue
                po = ((ath.get("position") or {})
                      .get("abbreviation") or "")
                r = out.setdefault(nm, {"tm": tm, "pos": po,
                                        "p": 0.0})
                if po and not r["pos"]:
                    r["pos"] = po
                for k, v in zip(ks, a.get("stats") or []):
                    if cn == KCAT and k == KKEY:
                        r["p"] += num(v)
                    elif cn != KCAT and k in PTS:
                        r["p"] += num(v) * PTS[k]
    return out

def week_events(wk, year=2026, stype=2):
    u = (BASE + "scoreboard?week=%d&seasontype=%d&"
         "dates=%d" % (wk, stype, year))
    d = get(u)
    ev = []
    for e in d.get("events", []):
        st = (e.get("status") or {}).get("type") or {}
        ev.append({"id": e["id"],
                   "name": e.get("shortName", ""),
                   "state": st.get("state"),
                   "detail": st.get("shortDetail")})
    return ev


# --- retry wrapper: a flaky read should not kill a build ---
import time as _t, socket as _sk
_sk.setdefaulttimeout(25)
_raw_get = get
def get(u, _tries=4):
    for _i in range(_tries):
        try:
            return _raw_get(u)
        except Exception as _e:
            if _i == _tries - 1:
                print("  fpts.get gave up (%s): %s" % (type(_e).__name__, u[-40:]))
                return None
            _t.sleep(1.5 * (_i + 1))
