import json
import math
import ssl
import time
import urllib.request
import certifi
import numpy as np
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
def get(u):
    r = urllib.request.Request(
        u, headers={"User-Agent": "curl/8.7.1"})
    with urllib.request.urlopen(
            r, timeout=25, context=CTX) as f:
        return json.loads(f.read().decode("utf-8",
                                          "ignore"))

GM = json.load(open("espn_lines_2025.json"))
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
FM = mk(W["mkt"])

def secs(cl, p):
    try:
        a, b = str(cl).split(":")
        c = int(a) * 60 + int(b)
    except Exception:
        c = 0
    return 1 if p > 4 else max(1, (4 - p) * 900 + c)

R = []
print("scoring %d games..." % len(GM))
for gi, g in enumerate(GM):
    try:
        d = get("https://site.api.espn.com/apis/site/v2/"
                "sports/football/nfl/summary?event="
                + str(g["ev"]))
    except Exception:
        continue
    cp = (((d.get("header") or {}).get("competitions")
           or [{}])[0])
    hw = None
    for x in (cp.get("competitors") or []):
        if x.get("homeAway") == "home":
            hw = 1 if x.get("winner") else 0
    if hw is None:
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
            o = FM(f)
            R.append({"g": gi, "ours": o if ph else 1 - o,
                      "espn": float(ewp[pid]),
                      "y": hw, "qtr": min(4, pn),
                      "sd": f["score_differential"],
                      "t": f["t"], "dn": f["down"],
                      "yl": f["yardline_100"],
                      "sp": f["spread_pos"],
                      "ph": 1 if ph else 0})
    if (gi + 1) % 20 == 0:
        print("  %d/%d" % (gi + 1, len(GM)))
    time.sleep(0.15)

D = pd.DataFrame(R)
D.to_csv("wp_h2h_plays.csv", index=False)
print("saved %d plays from %d games"
      % (len(D), D["g"].nunique()))

D = pd.read_csv("wp_h2h_plays.csv")
gs = sorted(D["g"].unique())
idx = {g: D.index[D["g"] == g].values for g in gs}
rng = np.random.default_rng(5)

def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-(y * np.log(p)
                   + (1 - y) * np.log(1 - p)).mean())

o = D["ours"].values
e = D["espn"].values
y = D["y"].values
obs = ll(e, y) - ll(o, y)
print("\n=== BOOTSTRAP OVER GAMES, 4000 RESAMPLES ===")
print("  observed edge (ESPN ll - ours ll): %+.4f" % obs)
di = []
for _ in range(4000):
    pick = rng.choice(gs, size=len(gs), replace=True)
    ii = np.concatenate([idx[g] for g in pick])
    di.append(ll(e[ii], y[ii]) - ll(o[ii], y[ii]))
di = np.array(di)
lo, hi = np.percentile(di, [2.5, 97.5])
print("  95%% CI: %+.4f to %+.4f" % (lo, hi))
print("  P(we beat ESPN): %.3f" % float((di > 0).mean()))
print("  verdict: %s"
      % ("significant" if lo > 0 else "NOT significant"))

print("\n=== CALIBRATION GAP, GAME-BOOTSTRAPPED ===")
def worst_gap(p, y):
    w = 0.0
    for b in np.arange(0, 1.0, 0.1):
        k = (p >= b) & (p < b + 0.1)
        if k.sum() < 100:
            continue
        w = max(w, abs(float(p[k].mean())
                       - float(y[k].mean())))
    return w
ws = []
for _ in range(500):
    pick = rng.choice(gs, size=len(gs), replace=True)
    ii = np.concatenate([idx[g] for g in pick])
    ws.append(worst_gap(o[ii], y[ii]))
ws = np.array(ws)
print("  observed worst gap: %.3f" % worst_gap(o, y))
print("  bootstrap 5th-95th: %.3f to %.3f"
      % tuple(np.percentile(ws, [5, 95])))
print("  nflverse holdout (800+ games) was 0.022")
print("\n  if the CI is wide, the 0.122 is sample noise,")
print("  not a broken model")
