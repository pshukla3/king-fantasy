import json
import numpy as np
import nflreadpy as nfl

BANDS = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
DEF = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
       "50_59": 5, "60_": 5, "miss": -1, "xpm": 1,
       "xpmiss": 0}
PRIOR = 60.0
import sys
CAL = float(sys.argv[1]) if len(sys.argv)>1 else 1.0

d = nfl.load_player_stats(list(range(2016, 2027))).to_pandas()
d = d[d["position"] == "K"].copy()
for c in (["fg_att", "fg_made", "pat_made", "pat_att"]
          + ["fg_made_" + b for b in BANDS]
          + ["fg_missed_" + b for b in BANDS]):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d["ord"] = d["season"] * 100 + d["week"]
d["act"] = (sum(d["fg_made_" + b] * DEF[b] for b in BANDS)
            + d["pat_made"] * DEF["xpm"]
            + sum(d["fg_missed_" + b] for b in BANDS)
            * DEF["miss"])
d = d[(d["fg_att"] + d["pat_att"]) > 0]
print("kicker games with a kick: %d" % len(d))

# team FG attempts per game, per season (opportunity proxy)
tm = d.groupby(["season", "team"], as_index=False).agg(
    fga=("fg_att", "sum"), xpa=("pat_att", "sum"),
    g=("week", "nunique"))
tm["fga_g"] = tm["fga"] / tm["g"]
tm["xpa_g"] = tm["xpa"] / tm["g"]
TFG = {(r["season"], r["team"]): r["fga_g"]
       for _, r in tm.iterrows()}
TXP = {(r["season"], r["team"]): r["xpa_g"]
       for _, r in tm.iterrows()}

res = []
for yr in range(2018, 2027):
    for wk in sorted(d[d["season"] == yr]["week"].unique()):
        cut = yr * 100 + wk
        tr = d[d["ord"] < cut]
        if len(tr) < 500:
            continue
        # league curve from everything before this week
        LG, SH = {}, {}
        tot = 0.0
        for b in BANDS:
            m = tr["fg_made_" + b].sum()
            a = m + tr["fg_missed_" + b].sum()
            LG[b] = m / a if a else 0.0
            SH[b] = a
            tot += a
        SH = {b: SH[b] / tot for b in BANDS}
        LGX = tr["pat_made"].sum() / max(1.0,
                                         tr["pat_att"].sum())
        prev = tr[tr["season"] >= yr - 1]
        LGF = (prev.groupby(["season", "team"])["fg_att"]
               .sum().mean() / 17.0) if len(prev) else 2.0
        LGF = float(np.clip(LGF, 1.5, 2.6))
        # league-average expected points (baseline 1)
        base_pts = sum(LGF * SH[b] * (LG[b] * DEF[b]
                       + (1 - LG[b]) * DEF["miss"])
                       for b in BANDS) + 2.4 * LGX

        cur = d[(d["season"] == yr) & (d["week"] == wk)]
        for _, r in cur.iterrows():
            h = tr[tr["player_id"] == r["player_id"]]
            if not len(h):
                continue
            rate, att = {}, {}
            for b in BANDS:
                m = float(h["fg_made_" + b].sum())
                a = m + float(h["fg_missed_" + b].sum())
                att[b] = a
                rate[b] = (m + PRIOR * LG[b]) / (a + PRIOR)
            t = sum(att.values())
            leg = ((att["50_59"] + att["60_"]) / t) if t else 0
            xp = ((h["pat_made"].sum() + 40 * LGX)
                  / (h["pat_att"].sum() + 40))
            fga = TFG.get((yr - 1, r["team"]), LGF)
            fga = 0.30 * fga + 0.70 * LGF
            xpa = TXP.get((yr - 1, r["team"]), 2.4)
            xpa = 0.30 * xpa + 0.70 * 2.4
            sh = dict(SH)
            tilt = leg - (SH["50_59"] + SH["60_"])
            sh["50_59"] += tilt * 0.7
            sh["40_49"] -= tilt * 0.4
            sh["30_39"] -= tilt * 0.3
            ss = sum(max(1e-6, v) for v in sh.values())
            sh = {b: max(1e-6, sh[b]) / ss for b in BANDS}
            proj = sum(fga * sh[b] * (rate[b] * DEF[b]
                       + (1 - rate[b]) * DEF["miss"])
                       for b in BANDS) + xpa * xp
            proj *= CAL
            ph = h[h["season"] == yr - 1]
            own = (ph["act"].mean() if len(ph) >= 4
                   else base_pts)
            res.append({"yr": yr, "wk": wk,
                        "act": r["act"], "mod": proj,
                        "lg": base_pts, "own": own})

R = {}
for x in res:
    R.setdefault(x["yr"], []).append(x)

def mae(a, p):
    return float(np.abs(np.array(a) - np.array(p)).mean())
def rmse(a, p):
    a, p = np.array(a), np.array(p)
    return float(np.sqrt(((a - p) ** 2).mean()))
def rr(a, p):
    a, p = np.array(a), np.array(p)
    return (float(np.corrcoef(a, p)[0, 1])
            if p.std() > 1e-9 else 0.0)

print("\n%-6s %6s %8s %8s %8s   %8s %8s"
      % ("SEASON", "N", "MODEL", "LG AVG", "OWN PY",
         "MODEL r", "ACT SD"))
print("-" * 62)
ALL = []
for yr in sorted(R):
    x = R[yr]
    ALL += x
    a = [i["act"] for i in x]
    print("%-6d %6d %8.3f %8.3f %8.3f   %+8.3f %8.2f"
          % (yr, len(x), mae(a, [i["mod"] for i in x]),
             mae(a, [i["lg"] for i in x]),
             mae(a, [i["own"] for i in x]),
             rr(a, [i["mod"] for i in x]), np.std(a)))
a = [i["act"] for i in ALL]
print("-" * 62)
print("%-6s %6d %8.3f %8.3f %8.3f   %+8.3f %8.2f"
      % ("ALL", len(ALL), mae(a, [i["mod"] for i in ALL]),
         mae(a, [i["lg"] for i in ALL]),
         mae(a, [i["own"] for i in ALL]),
         rr(a, [i["mod"] for i in ALL]), np.std(a)))
aa = np.array(a)
print("\n%-10s %9s %9s %9s" % ("", "RMSE", "MAE", "bias"))
for lbl, key in (("model", "mod"), ("league avg", "lg"),
                 ("own prior yr", "own")):
    p = np.array([i[key] for i in ALL])
    print("%-10s %9.3f %9.3f %+9.3f"
          % (lbl, rmse(aa, p), mae(aa, p), (p - aa).mean()))
print("\nactual: mean %.2f  median %.2f  skew %+.2f"
      % (aa.mean(), np.median(aa),
         float(((aa - aa.mean()) ** 3).mean()
               / aa.std() ** 3)))
m = np.array([i["mod"] for i in ALL])
print("\nmodel bias %+.3f | model sd %.2f | actual sd %.2f"
      % (np.mean(m - np.array(a)), m.std(), np.std(a)))
