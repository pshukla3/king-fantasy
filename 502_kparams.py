import json, re
import numpy as np
import nflreadpy as nfl

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

BANDS = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
# heavy prior: year-to-year persistence is near zero, so a
# kicker must show a LOT of evidence to move off the league
# curve. 60 attempts of prior per band-group.
PRIOR = 60.0

d = nfl.load_player_stats(list(range(2017, 2027))).to_pandas()
d = d[d["position"] == "K"].copy()
cols = ["fg_att", "fg_made", "pat_made", "pat_att"] + \
       ["fg_made_" + b for b in BANDS] + \
       ["fg_missed_" + b for b in BANDS]
for c in cols:
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d["ord"] = d["season"] * 100 + d["week"]
print("kicker weeks: %d  players: %d"
      % (len(d), d["player_id"].nunique()))

# league make rate per band
LG = {}
for b in BANDS:
    m = d["fg_made_" + b].sum()
    a = m + d["fg_missed_" + b].sum()
    LG[b] = float(m / a) if a > 0 else 0.0
    print("  league %-6s %5.1f%%  (%d att)" % (b, LG[b]*100, a))
LG_XP = float(d["pat_made"].sum() / max(1.0, d["pat_att"].sum()))
print("  league XP    %5.1f%%" % (LG_XP * 100))

# starter = most recent 2026 kicker per team by attempts
cur = d[d["season"] == 2026]
STARTER = {}
for tm, g in cur.groupby("team"):
    lw = g["week"].max()
    rec = g[g["week"] >= lw - 1]
    if len(rec):
        top = rec.groupby("player_display_name")[
            ["fg_att", "pat_att"]].sum()
        top["t"] = top["fg_att"] + top["pat_att"]
        STARTER[tm] = top.sort_values("t",
                                      ascending=False).index[0]
print("\nstarting kickers identified: %d teams" % len(STARTER))

OUT = {}
for pid, g in d.groupby("player_id"):
    g = g.sort_values("ord")
    nm = g["player_display_name"].iloc[-1]
    tm = g["team"].iloc[-1]
    # recency: last 3 seasons weigh most
    w = np.select(
        [g["season"].values >= 2026, g["season"].values == 2025,
         g["season"].values == 2024],
        [1.0, 0.7, 0.45], default=0.25)
    rate, att = {}, {}
    for b in BANDS:
        m = float((g["fg_made_" + b] * w).sum())
        a = m + float((g["fg_missed_" + b] * w).sum())
        att[b] = a
        # shrink HARD toward the league curve
        rate[b] = (m + PRIOR * LG[b]) / (a + PRIOR)
    xm = float((g["pat_made"] * w).sum())
    xa = float((g["pat_att"] * w).sum())
    xp = (xm + 40 * LG_XP) / (xa + 40)

    tot = sum(att.values())
    deep = att["50_59"] + att["60_"]
    # leg strength = share of his attempts from 50+
    legshare = deep / tot if tot > 0 else 0.0
    # sustained accuracy: overall make rate vs league, with
    # enough attempts to mean something
    allm = sum(float((g["fg_made_" + b] * w).sum())
               for b in BANDS)
    exp = sum(att[b] * LG[b] for b in BANDS)
    over = (allm - exp) / max(1.0, tot)

    OUT[norm(nm)] = {
        "n": nm, "tm": tm,
        "gms": int(len(g)),
        "att": round(float(tot), 1),
        "rate": {b: round(rate[b], 4) for b in BANDS},
        "xp": round(float(xp), 4),
        "legshare": round(float(legshare), 4),
        "over": round(float(over), 4),
        "starter": 1 if STARTER.get(tm) == nm else 0,
    }
json.dump(OUT, open("kparams.json", "w"), indent=0)
st = [v for v in OUT.values() if v["starter"]]
print("params for %d kickers (%d starters) -> kparams.json"
      % (len(OUT), len(st)))

st.sort(key=lambda x: -x["over"])
print("\n=== ACCURACY vs LEAGUE (shrunk, + is better) ===")
print("%-24s %-4s %6s %8s %9s"
      % ("KICKER", "TM", "ATT", "vs LG", "50+ SHARE"))
for v in st[:6]:
    print("%-24s %-4s %6.0f %+7.1f%% %8.1f%%"
          % (v["n"][:24], v["tm"], v["att"],
             v["over"] * 100, v["legshare"] * 100))
print("   ...")
for v in st[-6:]:
    print("%-24s %-4s %6.0f %+7.1f%% %8.1f%%"
          % (v["n"][:24], v["tm"], v["att"],
             v["over"] * 100, v["legshare"] * 100))

print("\n=== BIGGEST LEGS (50+ attempt share) ===")
st.sort(key=lambda x: -x["legshare"])
for v in st[:8]:
    print("   %-24s %-4s %5.1f%%  (50-59 make %.0f%%)"
          % (v["n"][:24], v["tm"], v["legshare"] * 100,
             v["rate"]["50_59"] * 100))
