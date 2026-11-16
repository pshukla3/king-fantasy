import json, re
import numpy as np
import nflreadpy as nfl

HALF = 3.0
REL = {"tshare": 0.657, "crate": 0.120, "ypr": 0.150,
       "tdt": 0.060, "tmatt": 0.500}
RELTE = dict(REL); RELTE["tshare"] = 0.604

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

print("loading receiving data")
d = nfl.load_player_stats([2025, 2026]).to_pandas()
for c in ("targets", "receptions", "receiving_yards",
          "receiving_tds"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d["ord"] = d["season"] * 100 + d["week"]

# team targets per game -> target share
tm = d.groupby(["season", "week", "team"],
               as_index=False)["targets"].sum()
tm = tm.rename(columns={"targets": "tmtgt"})
d = d.merge(tm, on=["season", "week", "team"], how="left")
d["tshare"] = np.where(d["tmtgt"] > 0,
                       d["targets"] / d["tmtgt"], 0.0)

r = d[d["position"].isin(["WR", "TE", "RB"])].copy()
r = r[r["targets"] >= 1]
ACTIVE = set(d[(d["season"] == 2026)
               & (d["targets"] >= 1)]["player_id"])
r = r[r["player_id"].isin(ACTIVE)]
print("pass-catchers with 2026 targets: %d"
      % r["player_id"].nunique())

POOL = {
    "tshare": float(r["targets"].sum() / r["tmtgt"].sum()),
    "crate": float(r["receptions"].sum() / r["targets"].sum()),
    "ypr": float(r["receiving_yards"].sum()
                 / max(1.0, r["receptions"].sum())),
    "tdt": float(r["receiving_tds"].sum() / r["targets"].sum()),
    "tmatt": float(tm["tmtgt"].mean()),
}
print("league baseline:", {k: round(v, 4)
                           for k, v in POOL.items()})

OUT = {}
for pid, g in r.groupby("player_id"):
    g = g.sort_values("ord")
    nm = g["player_display_name"].iloc[-1]
    pos = g["position"].iloc[-1]
    tmx = g["team"].iloc[-1]
    w = 0.5 ** (np.arange(len(g))[::-1] / HALF)
    w = w * np.where(g["season"].values >= 2026, 1.0, 0.30)
    neff = (w.sum() ** 2) / (w ** 2).sum()

    tg = max(1.0, (g["targets"] * w).sum())
    rc = max(1.0, (g["receptions"] * w).sum())
    raw = {
        "tshare": float((g["tshare"] * w).sum() / w.sum()),
        "crate": float((g["receptions"] * w).sum() / tg),
        "ypr": float((g["receiving_yards"] * w).sum() / rc),
        "tdt": float((g["receiving_tds"] * w).sum() / tg),
        "tmatt": float((g["tmtgt"] * w).sum() / w.sum()),
    }
    R = RELTE if pos == "TE" else REL
    sh = {}
    for k, rel in R.items():
        kk = neff * rel / (1 + (neff - 1) * rel) if neff > 1 else 0
        sh[k] = kk * raw[k] + (1 - kk) * POOL[k]
    OUT[norm(nm)] = {
        "n": nm, "pos": pos, "tm": tmx, "g": int(len(g)),
        "neff": round(float(neff), 2),
        "sd_t": float(g["targets"].std() or 2.0),
        "raw_ts": round(raw["tshare"], 4),
        **{k: float(v) for k, v in sh.items()},
    }
json.dump(OUT, open("wrparams.json", "w"), indent=0)
print("params for %d pass-catchers -> wrparams.json\n" % len(OUT))

print("=== HOW MUCH TARGET SHARE SURVIVES SHRINKAGE ===")
print("%-24s %-4s %7s %8s %8s %7s"
      % ("PLAYER", "POS", "N_EFF", "RAW TS", "SHRUNK", "KEPT"))
for k in ("jaxon smithnjigba", "jamarr chase",
          "amonra st brown", "puka nacua", "ceedee lamb",
          "drake london", "zay flowers", "trey mcbride",
          "justin jefferson", "nico collins"):
    v = OUT.get(k)
    if not v:
        continue
    kept = (v["tshare"] - POOL["tshare"]) / \
        max(1e-9, v["raw_ts"] - POOL["tshare"]) \
        if abs(v["raw_ts"] - POOL["tshare"]) > 1e-6 else 1.0
    print("%-24s %-4s %7.2f %7.1f%% %7.1f%% %6.0f%%"
          % (v["n"][:24], v["pos"], v["neff"],
             v["raw_ts"] * 100, v["tshare"] * 100, kept * 100))

print("\n=== 2026 TARGET SHARE LEADERS ===")
c = d[d["season"] == 2026]
a = c.groupby(["player_display_name", "position"],
              as_index=False).agg(
    ts=("tshare", "mean"), t=("targets", "mean"),
    y=("receiving_yards", "mean"), g=("targets", "size"))
a = a[(a["g"] >= 2) & a["position"].isin(["WR", "TE"])]
for _, x in a.sort_values("ts", ascending=False).head(12).iterrows():
    print("   %-24s %-3s %5.1f%% tgt share  %4.1f tgt/gm"
          "  %5.1f yd/gm"
          % (x["player_display_name"][:24], x["position"],
             x["ts"] * 100, x["t"], x["y"]))
