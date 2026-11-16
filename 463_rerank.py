import json, re, ssl, certifi
import numpy as np, pandas as pd
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
def get(u):
    return json.loads(U.urlopen(
        U.Request(u, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30, context=CTX).read())
def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

SET = json.load(open("site/_scoring.json"))
PM = json.load(open("site/_pmap.json"))
PROJ = json.load(open("site/_wkproj.json"))
B = json.load(open("site/_board.json"))
SKIP = {"pts_ppr", "pts_std", "pts_half_ppr", "gp",
        "gms_active", "tm_def_snp", "tm_off_snp",
        "tm_st_snp"}
def score(st):
    return sum(SET[k] * v for k, v in (st or {}).items()
               if k in SET and SET[k] and k not in SKIP)

BOARD = {norm(r["n"]): r for r in B["rows"]}
rows = []
for wk in ("1", "2", "3"):
    try:
        ST = get("https://api.sleeper.app/v1/stats/nfl/"
                 "regular/2026/%s" % wk)
    except Exception as e:
        print("week %s stats failed: %s" % (wk, str(e)[:60]))
        continue
    pj = PROJ.get(wk, {})
    n = 0
    for pid, st in ST.items():
        if str(pid).startswith("TEAM_"):
            continue
        m = PM.get(str(pid)) or {}
        nm = m.get("n")
        pos = m.get("p")
        if not nm or pos not in ("QB", "RB", "WR", "TE"):
            continue
        k = norm(nm)
        b = BOARD.get(k)
        if not b:
            continue
        act = score(st)
        rows.append({"wk": int(wk), "k": k, "n": nm,
                     "pos": pos, "act": act,
                     "ours": pj.get(k), "rk": b.get("rk"),
                     "adp": b.get("adp"),
                     "live": b.get("live")})
        n += 1
    print("week %s: %d players scored" % (wk, n))

R = pd.DataFrame(rows)
print("\nplayer-weeks: %d" % len(R))

print("\n=== which ranking predicts actual points better? ===")
print("  (correlation with what players actually scored)")
for lbl, col, invert in (("our weekly projection", "ours", 0),
                         ("board rank (consensus)", "rk", 1),
                         ("preseason ADP", "adp", 1)):
    s = R[R[col].notna() & R["act"].notna()]
    if len(s) < 50:
        print("  %-24s too few" % lbl)
        continue
    x = -s[col] if invert else s[col]
    r = np.corrcoef(x, s["act"])[0, 1]
    print("  %-24s n=%-5d r=%.4f" % (lbl, len(s), r))

print("\n=== accuracy of our weekly projection ===")
s = R[R["ours"].notna()]
for wk, g in s.groupby("wk"):
    e = g["ours"] - g["act"]
    print("  week %d  n=%-4d MAE %.2f  bias %+.2f"
          % (wk, len(g), e.abs().mean(), e.mean()))
e = s["ours"] - s["act"]
print("  ALL     n=%-4d MAE %.2f  bias %+.2f"
      % (len(s), e.abs().mean(), e.mean()))

print("\n=== biggest gaps: our rank vs season-to-date ===")
agg = (R.groupby(["k", "n", "pos"])
       .agg(gms=("act", "size"), ppg=("act", "mean"))
       .reset_index())
agg = agg[agg["gms"] >= 2]
agg["rk"] = agg["k"].map(lambda x: BOARD.get(x, {}).get("rk"))
agg["live"] = agg["k"].map(
    lambda x: BOARD.get(x, {}).get("live"))
agg = agg[agg["rk"].notna()]
agg["ppg_rk"] = agg["ppg"].rank(ascending=False)
agg["drift"] = agg["rk"] - agg["ppg_rk"]
print("\n  UNDERRATED by the board (scoring above rank):")
for _, r in agg.nlargest(12, "drift").iterrows():
    print("    %-22s %-3s rk#%-4.0f  ppg %5.1f (#%.0f)  "
          "drift %+.0f"
          % (r["n"][:22], r["pos"], r["rk"], r["ppg"],
             r["ppg_rk"], r["drift"]))
print("\n  OVERRATED by the board:")
for _, r in agg.nsmallest(12, "drift").iterrows():
    print("    %-22s %-3s rk#%-4.0f  ppg %5.1f (#%.0f)  "
          "drift %+.0f"
          % (r["n"][:22], r["pos"], r["rk"], r["ppg"],
             r["ppg_rk"], r["drift"]))
