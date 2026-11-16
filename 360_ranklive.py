import json, re, os, glob
import pandas as pd
import fpts
from importlib import import_module
dst = import_module("349_dst")

LAM = 0.185  # measured, walk-forward validated

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

ACT, DSTA = {}, {}
GP = {}
for w in range(1, fpts.nflweek() + 1):
    for e in fpts.week_events(w):
        if e["state"] != "post":
            continue
        s = fpts.get(fpts.BASE + "summary?event=" + e["id"])
        for nm, v in fpts.score_summary(s).items():
            k = norm(nm)
            ACT[k] = ACT.get(k, 0.0) + v["p"]
            GP[k] = GP.get(k, 0) + 1
        for t, d in dst.dst_from_summary(s).items():
            DSTA[t.upper()] = DSTA.get(t.upper(), 0.0) \
                + d["pts"]
print("scored players %d | defenses %d"
      % (len(ACT), len(DSTA)))

SNAP = {}
sp = "data_usage/snaps_2026.parquet"
if not os.path.exists(sp):
    try:
        import ssl, certifi
        import urllib.request as U
        CTX = ssl.create_default_context(
            cafile=certifi.where())
        u = ("https://github.com/nflverse/nflverse-data/"
             "releases/download/snap_counts/"
             "snap_counts_2026.parquet")
        open(sp, "wb").write(U.urlopen(
            U.Request(u, headers={"User-Agent": "curl/8.7.1"}),
            timeout=60, context=CTX).read())
    except Exception as e:
        print("2026 snaps unavailable: %s" % str(e)[:40])
if os.path.exists(sp):
    S = pd.read_parquet(sp)
    S["k"] = S["player"].map(norm)
    g = S.groupby("k")["offense_pct"].mean()
    SNAP = {k: float(v) for k, v in g.items()}
    print("snap share rows: %d" % len(SNAP))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["points"] = pd.to_numeric(B["points"], errors="coerce")

def obs(r):
    if str(r["position"]) == "DST":
        t = str(r.get("team") or "").upper()
        v = DSTA.get(t)
        n = 1 if v is not None else 0
        return (v, n)
    return (ACT.get(r["k"]), GP.get(r["k"], 0))

live, used = [], 0
for _, r in B.iterrows():
    base = r["points"]
    if pd.isna(base):
        live.append(None)
        continue
    tot, n = obs(r)
    if tot is None or n == 0:
        live.append(round(float(base), 2))
        continue
    ppg = tot / n
    # weight grows with games observed
    w = min(0.85, LAM * n)
    live.append(round((1 - w) * float(base) + w * ppg, 2))
    used += 1

B["proj_live"] = live
B["snap_pct"] = B["k"].map(lambda k: SNAP.get(k))
B = B.drop(columns=["k"])
B.to_csv("board_final.csv", index=False)
print("updated %d players with observed production" % used)

D = B[B["proj_live"].notna()].copy()
D["move"] = D["proj_live"] - D["points"]
D = D.sort_values("proj_live", ascending=False)
print("\n=== BIGGEST RISERS ===")
for _, r in D.sort_values("move", ascending=False)\
        .head(10).iterrows():
    print("  %-24s %-4s %5.2f -> %5.2f  %+5.2f"
          % (r["player_display_name"][:24], r["position"],
             r["points"], r["proj_live"], r["move"]))
print("\n=== BIGGEST FALLERS ===")
for _, r in D.sort_values("move").head(10).iterrows():
    print("  %-24s %-4s %5.2f -> %5.2f  %+5.2f"
          % (r["player_display_name"][:24], r["position"],
             r["points"], r["proj_live"], r["move"]))

rows = []
for i, (_, r) in enumerate(D.iterrows()):
    rows.append({"rk": i + 1,
                 "n": r["player_display_name"],
                 "pos": str(r["position"]),
                 "tm": str(r.get("team") or ""),
                 "base": round(float(r["points"]), 2),
                 "live": round(float(r["proj_live"]), 2),
                 "move": round(float(r["move"]), 2),
                 "snap": (round(float(r["snap_pct"]), 3)
                          if pd.notna(r.get("snap_pct"))
                          else None),
                 "inj": str(r.get("inj_status") or "")})
json.dump({"lam": LAM, "week": fpts.nflweek(),
           "rows": rows},
          open("site/_ranklive.json", "w"))
print("\nwrote site/_ranklive.json (%d players)" % len(rows))
