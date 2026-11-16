import json, re
import numpy as np
import nflreadpy as nfl

HALF = 5.0
# season-to-season measured: car_share .807, ypc .416
REL = {"cshare": 0.807, "ypc": 0.416, "tdc": 0.050,
       "tmcar": 0.500}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

d = nfl.load_player_stats([2024, 2025, 2026]).to_pandas()
for c in ("carries", "rushing_yards", "rushing_tds"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d["ord"] = d["season"] * 100 + d["week"]

try:
    sn = nfl.load_snap_counts([2024, 2025, 2026]).to_pandas()
    sn = sn[["season", "week", "player", "team", "offense_pct"]]
    sn["offense_pct"] = sn["offense_pct"].fillna(0).astype(float)
    if sn["offense_pct"].max() > 1.5:
        sn["offense_pct"] /= 100.0
    d = d.merge(sn, left_on=["season", "week",
                             "player_display_name", "team"],
                right_on=["season", "week", "player", "team"],
                how="left")
    d["snap"] = d["offense_pct"]
except Exception as e:
    print("snaps:", e)
    d["snap"] = np.nan

tc = d.groupby(["season", "week", "team"],
               as_index=False)["carries"].sum()
tc = tc.rename(columns={"carries": "tmcar"})
d = d.merge(tc, on=["season", "week", "team"], how="left")
d["cshare"] = np.where(d["tmcar"] > 0,
                       d["carries"] / d["tmcar"], 0.0)

r = d[d["position"].isin(["RB", "WR", "QB"])].copy()
r = r[r["carries"] >= 1]
ACT = set(d[(d["season"] == 2026)
            & (d["carries"] >= 1)]["player_id"])
r = r[r["player_id"].isin(ACT)]
r = r[r["position"] == "RB"]
print("RBs with 2026 carries: %d" % r["player_id"].nunique())

C = max(1.0, r["carries"].sum())
POOL = {"cshare": float(C / r["tmcar"].sum()),
        "ypc": float(r["rushing_yards"].sum() / C),
        "tdc": float(r["rushing_tds"].sum() / C),
        "tmcar": float(tc["tmcar"].mean())}
print("league RB baseline:",
      {k: round(v, 4) for k, v in POOL.items()})

OUT = {}
for pid, g in r.groupby("player_id"):
    g = g.sort_values("ord")
    nm = g["player_display_name"].iloc[-1]
    w = 0.5 ** (np.arange(len(g))[::-1] / HALF)
    _sy = g["season"].values
    w = w * np.select([_sy >= 2026, _sy == 2025, _sy == 2024],
                      [1.00, 0.55, 0.30], default=0.15)
    sp = g["snap"].values.astype(float)
    if np.isfinite(sp).sum() >= 3:
        base = np.nanmedian(sp[np.isfinite(sp)])
        if base and base > 0:
            rel = np.where(np.isfinite(sp),
                           np.clip(sp / base, 0, 1), 1.0)
            w = w * np.maximum(0.05, rel)
    neff = (w.sum() ** 2) / (w ** 2).sum()
    ca = max(1.0, (g["carries"] * w).sum())
    raw = {"cshare": float((g["cshare"] * w).sum() / w.sum()),
           "ypc": float((g["rushing_yards"] * w).sum() / ca),
           "tdc": float((g["rushing_tds"] * w).sum() / ca),
           "tmcar": float((g["tmcar"] * w).sum() / w.sum())}
    sh = {}
    for k, rel in REL.items():
        kk = neff * rel / (1 + (neff - 1) * rel) if neff > 1 else 0
        sh[k] = kk * raw[k] + (1 - kk) * POOL[k]
    OUT[norm(nm)] = {"n": nm, "tm": g["team"].iloc[-1],
                     "g": int(len(g)),
                     "neff": round(float(neff), 2),
                     "sd_c": float(g["carries"].std() or 3.0),
                     **{k: float(v) for k, v in sh.items()}}
json.dump(OUT, open("rbparams.json", "w"), indent=0)
print("\nparams for %d RBs -> rbparams.json" % len(OUT))
print("%-24s %-4s %7s %7s %7s %8s"
      % ("PLAYER", "TM", "CAR%", "CAR/G", "YPC", "TD/CAR"))
for k in ("jahmyr gibbs", "bijan robinson", "james cook",
          "omarion hampton", "derrick henry",
          "jonathan taylor", "kenneth walker",
          "saquon barkley", "bhayshul tuten"):
    v = OUT.get(k)
    if v:
        print("%-24s %-4s %6.1f%% %7.1f %7.2f %8.4f"
              % (v["n"][:24], v["tm"], v["cshare"] * 100,
                 v["tmcar"] * v["cshare"], v["ypc"], v["tdc"]))
