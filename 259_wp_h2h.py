import json
import ssl
import time
import urllib.request
import certifi
import nflreadpy as nfl

CTX = ssl.create_default_context(cafile=certifi.where())

def get(u):
    r = urllib.request.Request(
        u, headers={"User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(
            r, timeout=25, context=CTX) as f:
        return json.loads(f.read().decode("utf-8",
                                          "ignore"))

E2N = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX",
       "AZ": "ARI"}
def nz(x):
    return E2N.get(str(x), str(x))

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

S = pl(nfl.load_schedules(seasons=[2025]))
S = S[S["result"].notna() & S["spread_line"].notna()]
NV = {}
for _, r in S.iterrows():
    NV[(str(r["gameday"])[:10], nz(r["home_team"]))] = {
        "spread": float(r["spread_line"]),
        "away": nz(r["away_team"])}
print("nflverse 2025 games with a line: %d" % len(NV))
print("espn abbrevs seen vs nflverse keys checked"
      " via the join below")

DATES = ["20250907", "20250928", "20251019",
         "20251109", "20251130", "20251221"]
GM, miss = [], []
for dt in DATES:
    try:
        d = get("https://site.api.espn.com/apis/site/v2/"
                "sports/football/nfl/scoreboard?dates="
                + dt)
    except Exception as e:
        print("  %s FAILED %s" % (dt, e))
        continue
    ev = d.get("events") or []
    ok = 0
    for e in ev:
        c = (e.get("competitions") or [{}])[0]
        h = a = hid = None
        for x in (c.get("competitors") or []):
            ab = nz((x.get("team") or {})
                    .get("abbreviation"))
            if x.get("homeAway") == "home":
                h, hid = ab, str((x.get("team")
                                  or {}).get("id"))
            else:
                a = ab
        day = str(e.get("date"))[:10]
        rec = NV.get((day, h))
        if rec is None:
            miss.append("%s %s@%s" % (day, a, h))
            continue
        ok += 1
        GM.append({"ev": e.get("id"), "home": h,
                   "away": a, "hid": hid,
                   "spread": rec["spread"]})
    print("  %s  espn %2d  matched %2d" % (dt, len(ev), ok))
    time.sleep(0.3)

GM = GM[:60]
json.dump(GM, open("espn_lines_2025.json", "w"))
print("\nmatched %d | unmatched %d" % (len(GM), len(miss)))
for m in miss[:6]:
    print("  unmatched: %s" % m)
print("\nsample (spread is HOME perspective, nflverse):")
for g in GM[:5]:
    print("  %-4s @ %-4s  %+.1f" % (g["away"], g["home"],
                                    g["spread"]))

import math
import numpy as np

W = json.load(open("site/_wp.json"))

def mk(m):
    def f(d):
        z = m["intercept"]
        for i, k in enumerate(m["feat"]):
            z += ((d[k] - m["mean"][i]) / m["scale"][i]
                  * m["coef"][i])
        return 1.0 / (1.0 + math.exp(
            -max(-30.0, min(30.0, z))))
    return f

FM, FS = mk(W["mkt"]), mk(W["state"])

def secs(cl, p):
    try:
        a, b = str(cl).split(":")
        c = int(a) * 60 + int(b)
    except Exception:
        c = 0
    return 1 if p > 4 else max(1, (4 - p) * 900 + c)

OM, OS, ES, Y = [], [], [], []
bad = 0
print("\nscoring %d games..." % len(GM))
for i, g in enumerate(GM):
    try:
        d = get("https://site.api.espn.com/apis/site/v2/"
                "sports/football/nfl/summary?event="
                + str(g["ev"]))
    except Exception:
        bad += 1
        continue
    cp = (((d.get("header") or {}).get("competitions")
           or [{}])[0])
    hw = None
    for x in (cp.get("competitors") or []):
        if x.get("homeAway") == "home":
            hw = 1 if x.get("winner") else 0
    if hw is None:
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
            if ewp.get(pid) is None:
                continue
            pn = (p.get("period") or {}).get("number", 1)
            t = secs((p.get("clock") or {})
                     .get("displayValue"), pn)
            hs = p.get("homeScore") or 0
            aw = p.get("awayScore") or 0
            ph = (str((s.get("team") or {})
                      .get("id", "")) == g["hid"])
            sd = (hs - aw) if ph else (aw - hs)
            sp = g["spread"] if ph else -g["spread"]
            f = {"sd_t": sd / math.sqrt(t / 60.0 + 1),
                 "expt": math.exp(-4.0 * t / 3600.0),
                 "score_differential": sd, "t": t,
                 "half": t if t <= 1800 else t - 1800,
                 "down": s.get("down") or 1,
                 "ydstogo": s.get("distance") or 10,
                 "yardline_100":
                     s.get("yardsToEndzone") or 50,
                 "to_diff": 0,
                 "is4": 1 if s.get("down") == 4 else 0,
                 "spread_pos": sp}
            m, st = FM(f), FS(f)
            OM.append(m if ph else 1 - m)
            OS.append(st if ph else 1 - st)
            ES.append(float(ewp[pid]))
            Y.append(hw)
    if (i + 1) % 15 == 0:
        print("  %d/%d" % (i + 1, len(GM)))
    time.sleep(0.15)
print("collected %d plays | %d games skipped"
      % (len(Y), bad))

OM = np.clip(np.array(OM), 1e-6, 1 - 1e-6)
OS = np.clip(np.array(OS), 1e-6, 1 - 1e-6)
ES = np.clip(np.array(ES), 1e-6, 1 - 1e-6)
Y = np.array(Y)

def ll(p):
    return float(-(Y * np.log(p)
                   + (1 - Y) * np.log(1 - p)).mean())
def br(p):
    return float(((p - Y) ** 2).mean())

print("\n=== HEAD TO HEAD, %d PLAYS ===" % len(Y))
print("  %-18s %10s %10s" % ("model", "logloss",
                             "brier"))
print("  " + "-" * 40)
for nm, p in [("ours + market", OM),
              ("ours state only", OS),
              ("ESPN", ES)]:
    print("  %-18s %10.4f %10.4f" % (nm, ll(p), br(p)))
print("\n  market vs our state: %+.2f%%"
      % (100 * (1 - ll(OM) / ll(OS))))
print("  market vs ESPN     : %+.2f%%"
      % (100 * (1 - ll(OM) / ll(ES))))
print("  corr with ESPN     : %+.3f"
      % float(np.corrcoef(OM, ES)[0, 1]))
print("  mean abs diff      : %.3f"
      % float(np.abs(OM - ES).mean()))

print("\n=== OUR MARKET MODEL, CALIBRATION ===")
worst = 0.0
for lo in np.arange(0, 1.0, 0.1):
    k = (OM >= lo) & (OM < lo + 0.1)
    if k.sum() < 100:
        continue
    a, b = float(OM[k].mean()), float(Y[k].mean())
    worst = max(worst, abs(a - b))
    print("  %.1f-%.1f %7d  pred %.3f  actual %.3f %+.3f"
          % (lo, lo + 0.1, int(k.sum()), a, b, b - a))
print("\n  worst decile gap: %.3f" % worst)
print("\n  spread taken from nflverse (positive ="
      " home favored).")
print("  ESPN's live odds are INVERTED vs this and"
      " must be")
print("  negated in the browser. to_diff forced to 0 -"
      " ESPN")
print("  play objects carry no timeout counts.")

OM = np.clip(np.array(OM), 1e-6, 1 - 1e-6)
OS = np.clip(np.array(OS), 1e-6, 1 - 1e-6)
ES = np.clip(np.array(ES), 1e-6, 1 - 1e-6)
Y = np.array(Y)

def ll(p):
    return float(-(Y * np.log(p)
                   + (1 - Y) * np.log(1 - p)).mean())
def br(p):
    return float(((p - Y) ** 2).mean())

print("\n=== HEAD TO HEAD, %d PLAYS ===" % len(Y))
print("  %-18s %10s %10s" % ("model", "logloss",
                             "brier"))
print("  " + "-" * 40)
for nm, p in [("ours + market", OM),
              ("ours state only", OS),
              ("ESPN", ES)]:
    print("  %-18s %10.4f %10.4f" % (nm, ll(p), br(p)))
print("\n  market vs our state: %+.2f%%"
      % (100 * (1 - ll(OM) / ll(OS))))
print("  market vs ESPN     : %+.2f%%"
      % (100 * (1 - ll(OM) / ll(ES))))
print("  corr with ESPN     : %+.3f"
      % float(np.corrcoef(OM, ES)[0, 1]))
print("  mean abs diff      : %.3f"
      % float(np.abs(OM - ES).mean()))

print("\n=== OUR MARKET MODEL, CALIBRATION ===")
worst = 0.0
for lo in np.arange(0, 1.0, 0.1):
    k = (OM >= lo) & (OM < lo + 0.1)
    if k.sum() < 100:
        continue
    a, b = float(OM[k].mean()), float(Y[k].mean())
    worst = max(worst, abs(a - b))
    print("  %.1f-%.1f %7d  pred %.3f  actual %.3f %+.3f"
          % (lo, lo + 0.1, int(k.sum()), a, b, b - a))
print("\n  worst decile gap: %.3f" % worst)
print("\n  spread taken from nflverse (positive ="
      " home favored).")
print("  ESPN's live odds are INVERTED vs this and"
      " must be")
print("  negated in the browser. to_diff forced to 0 -"
      " ESPN")
print("  play objects carry no timeout counts.")
