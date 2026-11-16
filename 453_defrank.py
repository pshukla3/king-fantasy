import numpy as np, json
import nflreadpy as nfl

K_BLEND = 4.0   # games of 2026 needed to half-trust it

def agg(season):
    """Defensive allowances, from whatever source works."""
    d = nfl.load_player_stats(seasons=[season]).to_pandas()
    oc = "opponent_team"
    if oc not in d.columns:
        raise RuntimeError("no opponent_team column")
    for a, b in (("tgt", "targets"), ("rec", "receptions"),
                 ("ryd", "receiving_yards"),
                 ("rtd", "receiving_tds"),
                 ("car", "carries"),
                 ("rush", "rushing_yards"),
                 ("rutd", "rushing_tds")):
        d[a] = d.get(b, 0)
    g = (d.groupby([oc, "week"])
         .agg(att=("tgt", "sum"), rec=("rec", "sum"),
              pyd=("ryd", "sum"), ptd=("rtd", "sum"),
              car=("car", "sum"), rud=("rush", "sum"),
              rutd=("rutd", "sum"))
         .reset_index())
    out = {}
    for t, s in g.groupby(oc):
        n = len(s)
        out[t] = {
            "g": n,
            "pyd_g": s["pyd"].sum() / n,
            "ypa": s["pyd"].sum() / max(s["att"].sum(), 1),
            "cr": s["rec"].sum() / max(s["att"].sum(), 1),
            "ptd_g": s["ptd"].sum() / n,
            "rud_g": s["rud"].sum() / n,
            "ypcar": s["rud"].sum() / max(s["car"].sum(), 1),
            "rutd_g": s["rutd"].sum() / n,
        }
    return out


print("building defensive profiles")
try:
    P25 = agg(2025)
    print("  2025: %d defenses" % len(P25))
except Exception as e:
    P25 = {}
    print("  2025 failed: %s" % str(e)[:80])
try:
    P26 = agg(2026)
    print("  2026: %d defenses, %s games each"
          % (len(P26),
             sorted({v["g"] for v in P26.values()})))
except Exception as e:
    P26 = {}
    print("  2026 failed: %s" % str(e)[:80])

FLD = ["pyd_g", "ypa", "cr", "ptd_g",
       "rud_g", "ypcar", "rutd_g"]
teams = sorted(set(P25) | set(P26))
BL = {}
for t in teams:
    a, b = P25.get(t), P26.get(t)
    n26 = (b or {}).get("g", 0)
    w = n26 / (n26 + K_BLEND)
    BL[t] = {"g26": n26, "w26": round(w, 3)}
    for f in FLD:
        va = (a or {}).get(f)
        vb = (b or {}).get(f)
        if va is None and vb is None:
            continue
        if va is None:
            BL[t][f] = vb
        elif vb is None:
            BL[t][f] = va
        else:
            BL[t][f] = w * vb + (1 - w) * va
print("  blend weight on 2026: %.2f"
      % np.mean([v["w26"] for v in BL.values()]))

def rank(field, lower_is_better=True):
    vals = [(t, BL[t][field]) for t in BL if field in BL[t]]
    vals.sort(key=lambda x: x[1],
              reverse=not lower_is_better)
    return {t: i + 1 for i, (t, _) in enumerate(vals)}

# composite: pass rank from yards/gm, ypa, catch rate, TDs
pr = {}
for f in ("pyd_g", "ypa", "cr", "ptd_g"):
    r = rank(f)
    for t, v in r.items():
        pr[t] = pr.get(t, 0) + v
PASS = {t: i + 1 for i, (t, _) in
        enumerate(sorted(pr.items(), key=lambda x: x[1]))}

rr = {}
for f in ("rud_g", "ypcar", "rutd_g"):
    r = rank(f)
    for t, v in r.items():
        rr[t] = rr.get(t, 0) + v
RUSH = {t: i + 1 for i, (t, _) in
        enumerate(sorted(rr.items(), key=lambda x: x[1]))}

LG = {f: np.mean([BL[t][f] for t in BL if f in BL[t]])
      for f in FLD}

OUT = {}
for t in BL:
    OUT[t] = {
        "pass_rank": PASS.get(t), "rush_rank": RUSH.get(t),
        "g26": BL[t]["g26"], "w26": BL[t]["w26"],
        "pyd_g": round(BL[t].get("pyd_g", 0), 1),
        "rud_g": round(BL[t].get("rud_g", 0), 1),
        "m_ypa": round(BL[t].get("ypa", LG["ypa"])
                       / LG["ypa"], 3),
        "m_cr": round(BL[t].get("cr", LG["cr"])
                      / LG["cr"], 3),
        "m_ptd": round(BL[t].get("ptd_g", LG["ptd_g"])
                       / LG["ptd_g"], 3),
        "m_ypcar": round(BL[t].get("ypcar", LG["ypcar"])
                         / LG["ypcar"], 3),
        "m_rutd": round(BL[t].get("rutd_g", LG["rutd_g"])
                        / LG["rutd_g"], 3),
    }
json.dump({"league": {k: round(v, 3) for k, v in LG.items()},
           "def": OUT},
          open("site/_defrank.json", "w"),
          separators=(",", ":"))

print("\n=== PASS DEFENSE (1 = toughest) ===")
print("  %-4s %-5s %8s %6s %6s %6s"
      % ("RK", "TM", "YDS/G", "mYPA", "mCR", "mTD"))
for t in sorted(OUT, key=lambda x: OUT[x]["pass_rank"]):
    o = OUT[t]
    print("  %-4d %-5s %8.1f %6.3f %6.3f %6.3f"
          % (o["pass_rank"], t, o["pyd_g"], o["m_ypa"],
             o["m_cr"], o["m_ptd"]))

print("\n=== RUSH DEFENSE (1 = toughest) ===")
print("  %-4s %-5s %8s %8s %6s"
      % ("RK", "TM", "YDS/G", "mYPCAR", "mTD"))
for t in sorted(OUT, key=lambda x: OUT[x]["rush_rank"])[:16]:
    o = OUT[t]
    print("  %-4d %-5s %8.1f %8.3f %6.3f"
          % (o["rush_rank"], t, o["rud_g"], o["m_ypcar"],
             o["m_rutd"]))
print("wrote site/_defrank.json")
