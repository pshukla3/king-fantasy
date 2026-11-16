import json
import numpy as np
import pandas as pd

ALT = {"LA": "lar", "LAR": "lar", "WAS": "wsh",
       "JAX": "jax", "ARI": "ari", "LV": "lv"}
B = pd.read_csv("board_final.csv")
for c in ("pre_vorp", "upd_vorp", "pre_rank",
          "upd_rank"):
    if c not in B.columns:
        B[c] = B.get("vorp")
# rank_v is the final blended order: consensus base,
# model adjustment, bounded week-1 move, injury penalty.
# sorting by pre_vorp here would discard all of that.
if "rank_v" in B.columns:
    B = B[B["rank_v"].notna()].sort_values("rank_v")
else:
    B = B[B["pre_vorp"].notna()].sort_values(
        "pre_vorp", ascending=False)
B["posrk"] = B.groupby("position").cumcount() + 1

def sc100(col):
    mx = float(B[col].max())
    mn = float(B[col].quantile(0.02))
    return (100.0 * (B[col] - mn)
            / max(mx - mn, 1e-9)).clip(0, 100).round(0)
R = B["rank_v"].rank(method="min")
B["val100"] = (100.0 * (1.0 - (R - 1) / 220.0)
               ).clip(0, 100).round(0)
B["val100u"] = B["val100"]

# tiers: break where the value gap exceeds 2.2x median gap
v = list(B["vorp"].values)[:120]
gaps = [v[i] - v[i + 1] for i in range(len(v) - 1)]
med = sorted(gaps)[len(gaps) // 2] if gaps else 0.2
thr = max(0.25, med * 2.2)
tier, tiers = 1, []
for i in range(len(B)):
    tiers.append(tier)
    if i < len(gaps) and gaps[i] > thr and tier < 14:
        tier += 1
B["tier"] = tiers
print("tiers built: %d | threshold %.2f" % (tier, thr))

def g(r, c, d=None):
    x = r.get(c)
    return d if pd.isna(x) else x

rows = []
for i, (_, r) in enumerate(B.iterrows()):
    tm = str(g(r, "team", "") or "")
    rows.append({
        "rk": i + 1,
        "pid": str(g(r, "player_id", "") or ""),
        "img": str(g(r, "img", "") or ""),
        "part": (round(float(r["part"]), 2)
                 if not pd.isna(r.get("part"))
                 else None),
        "yrs": int(g(r, "yrs", 0) or 0),
        "lam": (round(float(r["lam"]), 3)
                if not pd.isna(r.get("lam"))
                else None),

        "n": r["player_display_name"],
        "pos": str(r["position"]),
        "tm": tm,
        "logo": ALT.get(tm.upper(), tm.lower()),
        "posrk": int(r["posrk"]),
        "tier": int(r["tier"]),
        "adp": (round(float(g(r, "adp", 0)), 1)
                if g(r, "adp") else None),
        "bye": int(g(r, "bye", 0) or 0),
        "sos": round(float(g(r, "sos", 0) or 0), 2),
        "risk": (round(float(r["inj_risk"]), 3)
                 if not pd.isna(r.get("inj_risk"))
                 else None),
        "games": (round(float(r["exp_g"]), 1)
                  if not pd.isna(r.get("exp_g")) else None),
        "floor": (round(float(r["p10"]), 1)
                  if not pd.isna(r.get("p10")) else None),
        "base": round(float(g(r, "points", 0) or 0), 1),
        "live": round(float(g(r, "proj_sch",
                              g(r, "points", 0)) or 0), 1),
        "ceil": (round(float(r["p90"]), 1)
                 if not pd.isna(r.get("p90")) else None),
        "vorp": round(float(r["pre_vorp"]), 2),
        "uvorp": round(float(r["upd_vorp"]), 2),
        "urk": int(r["upd_rank"]),
        "uval": int(r["val100u"]),
        "gm": (int(round(float(r["exp_g"])))
               if not pd.isna(r.get("exp_g")) else 17),
        "pid": str(g(r, "player_id", "") or ""),
        "img": str(g(r, "img", "") or ""),
        "val": int(r["val100"]),
        "inj": str(g(r, "inj_status", "") or ""),
    })
NT = 10
for r in rows:
    gm = r.get("gm") or 17
    if r.get("adp"):
        n = int(round(r["adp"]))
        r["adp_rp"] = "%d.%02d" % ((n - 1) // NT + 1,
                                   (n - 1) % NT + 1)
    else:
        r["adp_rp"] = None
    r["sos_pct"] = (round(100.0 * r["sos"]
                          / max(r["live"], 1), 1)
                    if r.get("live") else None)
    r["s_ds"] = round(r["base"] * gm)
    r["s_upd"] = round(r["live"] * gm)
    r["s_cons"] = round(r["base"] * gm)
    r["s_floor"] = (round(r["floor"] * gm)
                    if r.get("floor") is not None else None)
    r["s_ceil"] = (round(r["ceil"] * gm)
                   if r.get("ceil") is not None else None)

json.dump({"rows": rows, "n": len(rows)},
          open("site/_board.json", "w"))
print("wrote site/_board.json (%d players)" % len(rows))
print("\n%-3s %-22s %-7s %5s %5s %6s %5s %5s"
      % ("#", "PLAYER", "POS", "BYE", "SOS", "RISK",
         "LIVE", "VAL"))
for r in rows[:15]:
    print("%-3d %-22s %-3s%-4d %5d %+5.2f %5s %5.1f %5d"
          % (r["rk"], r["n"][:22], r["pos"], r["posrk"],
             r["bye"], r["sos"],
             ("%.0f%%" % (100 * r["risk"])
              if r["risk"] is not None else "-"),
             r["live"], r["val"]))
