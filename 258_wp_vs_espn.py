import json
import math
import ssl
import time
import urllib.request
import certifi
import numpy as np

CTX = ssl.create_default_context(cafile=certifi.where())

def get(u):
    r = urllib.request.Request(
        u, headers={"User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(
            r, timeout=25, context=CTX) as f:
        return json.loads(f.read().decode("utf-8",
                                          "ignore"))

M = json.load(open("site/_wp.json"))["state"]
def ours(f):
    z = M["intercept"]
    for i, k in enumerate(M["feat"]):
        z += ((f[k] - M["mean"][i]) / M["scale"][i]
              * M["coef"][i])
    return 1.0 / (1.0 + math.exp(-max(-30, min(30, z))))

def secs(cl, pd_):
    try:
        m, s = str(cl).split(":")
        c = int(m) * 60 + int(s)
    except Exception:
        c = 0
    if pd_ > 4:
        return 1
    return max(1, (4 - pd_) * 900 + c)

DATES = ["20250907", "20250914", "20250921",
         "20250928"]
EV = []
for dt in DATES:
    try:
        d = get("https://site.api.espn.com/apis/site/v2/"
                "sports/football/nfl/scoreboard?dates=" + dt)
        for e in (d.get("events") or []):
            EV.append(e.get("id"))
    except Exception as ex:
        print("scoreboard %s failed: %s" % (dt, ex))
EV = EV[:24]
print("games to score: %d" % len(EV))

OU, ES, Y = [], [], []
bad = 0
for i, ev in enumerate(EV):
    try:
        d = get("https://site.api.espn.com/apis/site/v2/"
                "sports/football/nfl/summary?event=" + ev)
    except Exception:
        bad += 1
        continue
    hd = (d.get("header") or {})
    cp = ((hd.get("competitions") or [{}])[0])
    cs = cp.get("competitors") or []
    hw = None
    hid = None
    for x in cs:
        if x.get("homeAway") == "home":
            hid = str((x.get("team") or {}).get("id"))
            hw = 1 if x.get("winner") else 0
    if hw is None or hid is None:
        bad += 1
        continue
    ewp = {}
    for w in (d.get("winprobability") or []):
        if w.get("playId") is not None:
            ewp[str(w["playId"])] = w.get(
                "homeWinPercentage")
    for dr in ((d.get("drives") or {}).get("previous")
               or []):
        for p in (dr.get("plays") or []):
            s = p.get("start") or {}
            if not s.get("down"):
                continue
            pid = str(p.get("id"))
            if pid not in ewp or ewp[pid] is None:
                continue
            pdn = (p.get("period") or {}).get("number", 1)
            t = secs((p.get("clock") or {})
                     .get("displayValue"), pdn)
            hs = p.get("homeScore") or 0
            as_ = p.get("awayScore") or 0
            tid = str((s.get("team") or {}).get("id", ""))
            ph = (tid == hid)
            sd = (hs - as_) if ph else (as_ - hs)
            y2e = s.get("yardsToEndzone")
            if y2e is None:
                y2e = 50
            f = {"sd_t": sd / math.sqrt(t / 60.0 + 1),
                 "expt": math.exp(-4.0 * t / 3600.0),
                 "score_differential": sd, "t": t,
                 "half": t if t <= 1800 else t - 1800,
                 "down": s.get("down") or 1,
                 "ydstogo": s.get("distance") or 10,
                 "yardline_100": y2e,
                 "to_diff": 0,
                 "is4": 1 if s.get("down") == 4 else 0}
            o = ours(f)
            OU.append(o if ph else 1 - o)
            ES.append(float(ewp[pid]))
            Y.append(hw)
    time.sleep(0.2)

OU = np.clip(np.array(OU), 1e-6, 1 - 1e-6)
ES = np.clip(np.array(ES), 1e-6, 1 - 1e-6)
Y = np.array(Y)
print("plays compared: %d | games skipped: %d"
      % (len(Y), bad))
if len(Y) > 500:
    def ll(p):
        return float(-(Y * np.log(p)
                       + (1 - Y) * np.log(1 - p)).mean())
    def br(p):
        return float(((p - Y) ** 2).mean())
    print("\n  %-14s %10s %10s" % ("model", "logloss",
                                   "brier"))
    print("  " + "-" * 36)
    print("  %-14s %10.4f %10.4f"
          % ("ours (state)", ll(OU), br(OU)))
    print("  %-14s %10.4f %10.4f"
          % ("ESPN", ll(ES), br(ES)))
    print("\n  correlation ours vs ESPN: %+.3f"
          % float(np.corrcoef(OU, ES)[0, 1]))
    print("  mean abs difference: %.3f"
          % float(np.abs(OU - ES).mean()))
else:
    print("not enough plays matched to compare")
