import json, re
import numpy as np
import nflreadpy as nfl

YR = [2024, 2025, 2026]
d = nfl.load_player_stats(YR).to_pandas()
for c in ("attempts", "passing_yards", "passing_tds",
          "passing_interceptions", "sacks_suffered",
          "sack_yards_lost"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
q = d[(d["position"] == "QB") & (d["attempts"] >= 10)].copy()

# ANY/A: the standard single-number passing quality stat
den = (q["attempts"] + q["sacks_suffered"]).clip(lower=1)
q["anya"] = ((q["passing_yards"] - q["sack_yards_lost"]
              + 20 * q["passing_tds"]
              - 45 * q["passing_interceptions"]) / den)
LG = float(q["anya"].mean())
print("league ANY/A = %.2f" % LG)

# a QB's quality = his own multi-game ANY/A, shrunk
agg = q.groupby("player_display_name", as_index=False).agg(
    anya=("anya", "mean"), n=("anya", "size"))
agg["q"] = np.where(
    agg["n"] >= 4,
    (agg["n"] * agg["anya"] + 6 * LG) / (agg["n"] + 6) / LG,
    1.0)
QUAL = dict(zip(agg["player_display_name"], agg["q"]))

# who started each team-week -> that week's quality factor
HIST = {}
for (s, w, t), g in q.groupby(["season", "week", "team"]):
    st = g.sort_values("attempts", ascending=False)
    nm = st["player_display_name"].iloc[0]
    HIST["%d-%d-%s" % (s, w, t)] = round(
        float(np.clip(QUAL.get(nm, 1.0), 0.72, 1.32)), 4)

print("\n=== BEST / WORST QB SITUATIONS (2024-26) ===")
a = agg[agg["n"] >= 6].sort_values("q", ascending=False)
for _, r in a.head(6).iterrows():
    print("   %-24s %.3f  (ANY/A %.2f)"
          % (r["player_display_name"][:24], r["q"], r["anya"]))
print("   ...")
for _, r in a.tail(6).iterrows():
    print("   %-24s %.3f  (ANY/A %.2f)"
          % (r["player_display_name"][:24], r["q"], r["anya"]))

# CURRENT quality per team: who is actually throwing now
try:
    QP = json.load(open("qbparams.json"))
except Exception:
    QP = {}
try:
    INJ = json.load(open("site/_injtime.json"))
except Exception:
    INJ = {}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

CUR = {}
for k, p in QP.items():
    t = p.get("tm")
    if not t:
        continue
    CUR.setdefault(t, []).append(p)
NOW = {}
for t, lst in CUR.items():
    starters = [p for p in lst if p.get("qb1")]
    hurt = [p for p in starters
            if norm(p["n"]) in INJ
            and INJ[norm(p["n"])]["weeks"] > 0]
    if starters and not hurt:
        NOW[t] = np.clip(QUAL.get(starters[0]["n"], 1.0),
                         .72, 1.32)
    else:
        # starter is out -> next man's quality, floored
        back = [p for p in lst if not p.get("qb1")]
        bq = max([QUAL.get(p["n"], 0.88) for p in back],
                 default=0.88)
        NOW[t] = float(np.clip(min(bq, 0.95), 0.72, 1.10))
NOW = {t: round(float(v), 4) for t, v in NOW.items()}
json.dump({"hist": HIST, "now": NOW, "lg": round(LG, 3)},
          open("qbindex.json", "w"), separators=(",", ":"))
print("\nwrote qbindex.json (%d team-weeks, %d teams now)"
      % (len(HIST), len(NOW)))

print("\n=== CURRENT QB SITUATION BY TEAM ===")
for t, v in sorted(NOW.items(), key=lambda x: -x[1])[:6]:
    print("   %-5s %.3f" % (t, v))
print("   ...")
for t, v in sorted(NOW.items(), key=lambda x: -x[1])[-8:]:
    print("   %-5s %.3f%s" % (t, v,
          "   <-- starter out" if v < 0.96 else ""))
