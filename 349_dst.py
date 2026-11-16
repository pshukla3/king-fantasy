import json, ssl, certifi, re
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
B = ("https://site.api.espn.com/apis/site/v2/"
     "sports/football/nfl/")

def g(u):
    return json.loads(U.urlopen(U.Request(u, headers=H),
                      timeout=25, context=CTX).read())

def patier(pa):
    if pa == 0:
        return 10.0
    if pa <= 6:
        return 7.0
    if pa <= 13:
        return 4.0
    if pa <= 20:
        return 1.0
    if pa <= 27:
        return 0.0
    if pa <= 34:
        return -1.0
    return -4.0

def num(v, idx=0):
    s = str(v or "0")
    parts = re.split(r"[-/]", s)
    try:
        return float(parts[idx])
    except (ValueError, IndexError):
        return 0.0

def dst_from_summary(s):
    """-> {TEAM: {pts, sacks, ints, fr, td, pa}}"""
    tm = (s.get("boxscore") or {}).get("teams") or []
    if len(tm) < 2:
        return {}
    stat, ab = {}, {}
    for i, t in enumerate(tm):
        a = (t.get("team") or {}).get("abbreviation", "")
        ab[i] = a
        d = {}
        for st in (t.get("statistics") or []):
            d.setdefault(st.get("name"), st.get(
                "displayValue"))
        stat[i] = d
    sc = {}
    for c in ((s.get("header") or {}).get("competitions")
              or [])[:1]:
        for x in c.get("competitors", []):
            sc[(x.get("team") or {}).get("abbreviation")] = \
                int(x.get("score") or 0)
    saf = 0
    for p in (s.get("scoringPlays") or []):
        if "safety" in ((p.get("type") or {})
                        .get("text", "")).lower():
            saf += 1
    out = {}
    for i in (0, 1):
        me, opp = ab[i], ab[1 - i]
        o = stat[1 - i]
        sacks = num(o.get("sacksYardsLost"), 0)
        ints = num(o.get("interceptions"), 0)
        fr = num(o.get("fumblesLost"), 0)
        td = num(stat[i].get("defensiveTouchdowns"), 0)
        pa = sc.get(opp, 0)
        pts = (sacks * 1.0 + ints * 2.0 + fr * 2.0
               + td * 6.0 + patier(pa))
        out[me] = {"pts": round(pts, 2), "sacks": sacks,
                   "ints": ints, "fr": fr, "td": td,
                   "pa": pa}
    return out

if __name__ == "__main__":
    sb = g(B + "scoreboard?week=1&seasontype=2&dates=2026")
    ev = [(e["id"], e.get("shortName"))
          for e in sb.get("events", [])
          if ((e.get("status") or {}).get("type")
              or {}).get("state") == "post"]
    print("final games: %d\n" % len(ev))
    print("%-5s %6s %6s %5s %4s %4s %5s"
          % ("TEAM", "PTS", "SACKS", "INT", "FR", "TD", "PA"))
    print("-" * 42)
    for eid, nm in ev:
        for t, d in dst_from_summary(
                g(B + "summary?event=" + eid)).items():
            print("%-5s %6.1f %6.0f %5.0f %4.0f %4.0f %5d"
                  % (t, d["pts"], d["sacks"], d["ints"],
                     d["fr"], d["td"], d["pa"]))
