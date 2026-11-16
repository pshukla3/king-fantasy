import json, re
import numpy as np
import nflreadpy as nfl

BANDS = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
PTS = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
       "50_59": 5, "60_": 5}
XP_PT, MISS = 1.0, -1.0
PRIOR = 60.0

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

d = nfl.load_player_stats(list(range(2017, 2027))).to_pandas()
d = d[d["position"] == "K"].copy()
for c in (["fg_att", "fg_made", "pat_made", "pat_att"]
          + ["fg_made_" + b for b in BANDS]
          + ["fg_missed_" + b for b in BANDS]):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)

TRAIN = d[d["season"] <= 2025]          # BLIND to 2026
LG, SH = {}, {}
tot = 0.0
for b in BANDS:
    m = TRAIN["fg_made_" + b].sum()
    a = m + TRAIN["fg_missed_" + b].sum()
    LG[b] = float(m / a) if a else 0.0
    SH[b] = float(a)
    tot += a
for b in BANDS:
    SH[b] = SH[b] / tot
LG_XP = float(TRAIN["pat_made"].sum()
              / max(1.0, TRAIN["pat_att"].sum()))

# team FG opportunity, 2025 only
p = nfl.load_pbp([2025]).to_pandas()
p = p[p["posteam"].notna()]
dv = p.groupby(["season", "week", "posteam", "defteam",
                "drive"], as_index=False).agg(
    res=("fixed_drive_result", "first"))
dv = dv[dv["res"].notna()]
dv["att"] = dv["res"].str.contains("Field goal|Missed",
                                   na=False, regex=True)
dv["td"] = dv["res"].str.contains("Touchdown", na=False)
og = dv.groupby("posteam").agg(a=("att", "sum"),
                               t=("td", "sum"),
                               g=("week", "nunique"))
og["fga"] = og.a / og.g
og["tdg"] = og.t / og.g
dg = dv.groupby("defteam").agg(a=("att", "sum"),
                               g=("week", "nunique"))
dg["fga"] = dg.a / dg.g
LGF = float(og["fga"].mean())
LGD = float(dg["fga"].mean())
LGT = float(og["tdg"].mean())
print("2025 league: %.2f FG att/gm, %.2f TD/gm" % (LGF, LGT))

# per-kicker shrunk rates on TRAIN only
K = {}
for pid, g in TRAIN.groupby("player_id"):
    g = g.sort_values(["season", "week"])
    w = np.select([g["season"].values == 2025,
                   g["season"].values == 2024],
                  [1.0, 0.7], default=0.35)
    rate, att = {}, {}
    for b in BANDS:
        m = float((g["fg_made_" + b] * w).sum())
        a = m + float((g["fg_missed_" + b] * w).sum())
        att[b] = a
        rate[b] = (m + PRIOR * LG[b]) / (a + PRIOR)
    xm = float((g["pat_made"] * w).sum())
    xa = float((g["pat_att"] * w).sum())
    t = sum(att.values())
    K[norm(g["player_display_name"].iloc[-1])] = {
        "n": g["player_display_name"].iloc[-1],
        "rate": rate, "att": t,
        "xp": (xm + 40 * LG_XP) / (xa + 40),
        "leg": (att["50_59"] + att["60_"]) / t if t else 0.0}

# who actually kicked in week 1 2026, and what they scored
w1 = d[(d["season"] == 2026) & (d["week"] == 1)]
w1 = w1[(w1["fg_att"] + w1["pat_att"]) > 0]
sc = nfl.load_schedules([2026]).to_pandas()
sc = sc[sc["week"] == 1]
OPP = {}
for _, g in sc.iterrows():
    OPP[g["home_team"]] = (g["away_team"], 1)
    OPP[g["away_team"]] = (g["home_team"], 0)

def actual(r):
    pts = sum(r["fg_made_" + b] * PTS[b] for b in BANDS)
    miss = sum(r["fg_missed_" + b] for b in BANDS)
    return pts + r["pat_made"] * XP_PT + miss * MISS

rows = []
for _, r in w1.iterrows():
    tm = r["team"]
    k = K.get(norm(r["player_display_name"]))
    if not k or tm not in OPP:
        continue
    opp, home = OPP[tm]
    # expected attempts: team rate shrunk hard to league
    # (year-to-year r ~ 0), then matchup
    tfga = og["fga"].get(tm, LGF)
    base = 0.35 * tfga + 0.65 * LGF
    dadj = (dg["fga"].get(opp, LGD) / LGD) if LGD else 1.0
    dadj = min(1.25, max(0.80, dadj))
    exp_att = base * dadj
    # distance mix: league shares, tilted by his leg
    sh = dict(SH)
    tilt = k["leg"] - (SH["50_59"] + SH["60_"])
    sh["50_59"] += tilt * 0.6
    sh["30_39"] -= tilt * 0.3
    sh["40_49"] -= tilt * 0.3
    ssum = sum(max(0.0, v) for v in sh.values())
    sh = {b: max(0.0, v) / ssum for b, v in sh.items()}
    proj = 0.0
    for b in BANDS:
        a = exp_att * sh[b]
        proj += a * k["rate"][b] * PTS[b]
        proj += a * (1 - k["rate"][b]) * MISS
    xpa = (og["tdg"].get(tm, LGT) * 0.35 + LGT * 0.65)
    proj += xpa * k["xp"] * XP_PT
    rows.append({"n": k["n"], "tm": tm, "opp": opp,
                 "proj": proj, "act": actual(r),
                 "att": r["fg_att"], "made": r["fg_made"]})

rows.sort(key=lambda x: -x["proj"])
print("\n=== WEEK 1 2026 — PROJECTED BLIND vs ACTUAL ===")
print("%-24s %-4s %-5s %7s %7s %7s %5s"
      % ("KICKER", "TM", "OPP", "PROJ", "ACTUAL", "ERR", "FG"))
for r in rows:
    print("%-24s %-4s %-5s %7.2f %7.1f %+7.2f %2d/%d"
          % (r["n"][:24], r["tm"], r["opp"], r["proj"],
             r["act"], r["act"] - r["proj"],
             r["made"], r["att"]))
if rows:
    e = np.array([r["act"] - r["proj"] for r in rows])
    a = np.array([r["act"] for r in rows])
    p = np.array([r["proj"] for r in rows])
    print("\nn=%d   MAE %.2f   bias %+.2f   r %.3f"
          % (len(rows), np.abs(e).mean(), e.mean(),
             np.corrcoef(a, p)[0, 1] if len(rows) > 2 else 0))
    print("projection spread: %.2f to %.2f  (sd %.2f)"
          % (p.min(), p.max(), p.std()))
    print("actual spread:     %.1f to %.1f  (sd %.2f)"
          % (a.min(), a.max(), a.std()))
