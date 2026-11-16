import json, re
import numpy as np
import nflreadpy as nfl

HALF = 5.0
# SEASON-to-season reliability, not week-to-week.
# We are projecting a season, so weekly noise must not
# decide how much of a player's skill we keep.
import os
_S = {}
if os.path.exists("seasonrel.json"):
    _S = json.load(open("seasonrel.json"))
REL = {"tshare": 0.827,
       "adot": max(0.40, _S.get("adot", 0.55)),
       "yac": max(0.30, _S.get("yacr", 0.40)),
       "crate": max(0.25, _S.get("crate", 0.275)),
       "tdt": 0.030, "tmatt": 0.500}
RELTE = dict(REL); RELTE["tshare"] = 0.810

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

d = nfl.load_player_stats([2024, 2025, 2026]).to_pandas()
YAC = ("receiving_yards_after_catch"
       if "receiving_yards_after_catch" in d.columns else None)
print("YAC column:", YAC)
need = ["targets", "receptions", "receiving_yards",
        "receiving_tds", "receiving_air_yards"]
if YAC:
    need.append(YAC)
for c in need:
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d["ord"] = d["season"] * 100 + d["week"]

# --- strip QB quality out of a player's history ---
# Target share is a ROLE and is QB-independent, so it is
# left alone. Yards and TDs depend heavily on who throws.
try:
    _QI = json.load(open("qbindex.json"))
    _H = _QI["hist"]
    _qf = np.array([_H.get("%d-%d-%s" % (a1, b1, c1), 1.0)
                    for a1, b1, c1
                    in zip(d["season"], d["week"], d["team"])])
    _qf = np.clip(_qf, 0.72, 1.32)
    d["receiving_yards"] = d["receiving_yards"] / _qf
    d["receiving_tds"] = d["receiving_tds"] / _qf
    d["receiving_air_yards"] = d["receiving_air_yards"] / _qf
    d["receptions"] = d["receptions"] / np.sqrt(_qf)
    print("QB-quality neutralised across %d rows" % len(d))
except Exception as _e:
    print("qbindex unavailable:", _e)

# --- snap share: a game he left early is not evidence ---
try:
    _sn = nfl.load_snap_counts([2024, 2025, 2026]).to_pandas()
    _sn = _sn[["season", "week", "player", "team",
               "offense_pct"]].copy()
    _sn["offense_pct"] = _sn["offense_pct"].fillna(
        0.0).astype(float)
    if _sn["offense_pct"].max() > 1.5:
        _sn["offense_pct"] = _sn["offense_pct"] / 100.0
    d = d.merge(_sn, left_on=["season", "week",
                              "player_display_name", "team"],
                right_on=["season", "week", "player", "team"],
                how="left")
    d["snap"] = d["offense_pct"]
    print("snap data matched on %.0f%% of rows"
          % (d["snap"].notna().mean() * 100))
except Exception as _e:
    print("snap counts unavailable:", _e)
    d["snap"] = np.nan

# measure YAC stability before trusting it
if YAC:
    z = d[(d["position"].isin(["WR", "TE"]))
          & (d["receptions"] >= 2)].copy()
    z["yacr"] = z[YAC] / z["receptions"]
    xs, ys = [], []
    for pid, g in z.groupby("player_id"):
        v = g.sort_values("ord")["yacr"].values
        for i in range(len(v) - 1):
            xs.append(v[i]); ys.append(v[i + 1])
    if len(xs) > 50:
        print("YAC per reception, week-to-week r = %.3f (n=%d)"
              % (np.corrcoef(xs, ys)[0, 1], len(xs)))

tm = d.groupby(["season", "week", "team"],
               as_index=False)["targets"].sum()
tm = tm.rename(columns={"targets": "tmtgt"})
d = d.merge(tm, on=["season", "week", "team"], how="left")
d["tshare"] = np.where(d["tmtgt"] > 0,
                       d["targets"] / d["tmtgt"], 0.0)

r = d[d["position"].isin(["WR", "TE", "RB"])].copy()
r = r[r["targets"] >= 1]
ACT = set(d[(d["season"] == 2026)
            & (d["targets"] >= 1)]["player_id"])
r = r[r["player_id"].isin(ACT)]

T = max(1.0, r["targets"].sum())
C = max(1.0, r["receptions"].sum())
POOL = {"tshare": float(r["targets"].sum() / r["tmtgt"].sum()),
        "adot": float(r["receiving_air_yards"].sum() / T),
        "yac": float(r[YAC].sum() / C) if YAC else 4.5,
        "crate": float(C / T),
        "tdt": float(r["receiving_tds"].sum() / T),
        "tmatt": float(tm["tmtgt"].mean())}
print("league:", {k: round(v, 3) for k, v in POOL.items()})

OUT = {}
for pid, g in r.groupby("player_id"):
    g = g.sort_values("ord")
    nm = g["player_display_name"].iloc[-1]
    pos = g["position"].iloc[-1]
    w = 0.5 ** (np.arange(len(g))[::-1] / HALF)
    _sy = g["season"].values
    w = w * np.select(
        [_sy >= 2026, _sy == 2025, _sy == 2024],
        [1.00, 0.55, 0.30], default=0.15)
    # A 12%-snap game is 12% of a game's worth of evidence.
    # Measured: partial games understate a player by 75%.
    _sp = g["snap"].values.astype(float)
    if np.isfinite(_sp).sum() >= 3:
        _base = np.nanmedian(_sp[np.isfinite(_sp)])
        if _base and _base > 0:
            _rel = np.where(np.isfinite(_sp),
                            np.clip(_sp / _base, 0.0, 1.0), 1.0)
            w = w * np.maximum(0.05, _rel)
    neff = (w.sum() ** 2) / (w ** 2).sum()
    tg = max(1.0, (g["targets"] * w).sum())
    rc = max(1.0, (g["receptions"] * w).sum())
    raw = {"tshare": float((g["tshare"] * w).sum() / w.sum()),
           "adot": float((g["receiving_air_yards"] * w).sum() / tg),
           "yac": float((g[YAC] * w).sum() / rc) if YAC else POOL["yac"],
           "crate": float(rc / tg),
           "tdt": float((g["receiving_tds"] * w).sum() / tg),
           "tmatt": float((g["tmtgt"] * w).sum() / w.sum())}
    R = RELTE if pos == "TE" else REL
    sh = {}
    for k, rel in R.items():
        kk = neff * rel / (1 + (neff - 1) * rel) if neff > 1 else 0
        sh[k] = kk * raw[k] + (1 - kk) * POOL[k]
    OUT[norm(nm)] = {"n": nm, "pos": pos,
                     "tm": g["team"].iloc[-1],
                     "g": int(len(g)),
                     "neff": round(float(neff), 2),
                     "sd_t": float(g["targets"].std() or 2.0),
                     **{k: float(v) for k, v in sh.items()}}
json.dump(OUT, open("wrparams.json", "w"), indent=0)
print("\nparams for %d pass-catchers" % len(OUT))
print("%-24s %-4s %6s %6s %6s %6s %7s"
      % ("PLAYER", "POS", "TSHR", "aDOT", "YAC", "CATCH", "TD/TGT"))
for k in ("jaxon smithnjigba", "jamarr chase",
          "amonra st brown", "puka nacua", "chris olave",
          "zay flowers", "ceedee lamb", "trey mcbride"):
    v = OUT.get(k)
    if v:
        print("%-24s %-4s %5.1f%% %6.1f %6.1f %5.0f%% %7.4f"
              % (v["n"][:24], v["pos"], v["tshare"] * 100,
                 v["adot"], v["yac"], v["crate"] * 100, v["tdt"]))
