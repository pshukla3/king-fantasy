import json, re, os
import numpy as np
import nflreadpy as nfl

SIMS = 20000
HALF = 3.0
np.random.seed(7)

# measured week-to-week reliability per component.
# passing efficiency is nearly noise (r=.119 on points),
# rushing volume is the real signal (r=.315).
REL = {"att": 0.394, "ypa": 0.150, "ptd": 0.100,
       "int": 0.050, "car": 0.463, "ypc": 0.200,
       "rtd": 0.080}

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

print("loading QB history")
d = nfl.load_player_stats([2025, 2026]).to_pandas()
d = d[d["position"] == "QB"].copy()
for c in ("attempts", "passing_yards", "passing_tds",
          "passing_interceptions", "carries",
          "rushing_yards", "rushing_tds"):
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)
d["ord"] = d["season"] * 100 + d["week"]
d = d.sort_values("ord")
LASTORD = d["ord"].max()

# only games he actually started
st = d[d["attempts"] >= 12].copy()

# must have actually played in 2026 -- otherwise we
# project retired and departed players off old data
ACTIVE = set(d[(d["season"] == 2026)
               & (d["attempts"] >= 1)]["player_id"])
st = st[st["player_id"].isin(ACTIVE)]
print("QBs with 2026 snaps: %d" % st["player_id"].nunique())

# QB1 = most attempts in his team's most recent 2026 game
# QB1 = the team's established starter by SEASON volume,
# not by who threw last week. An injured starter who misses
# a game is still the starter -- using "most recent game"
# demoted Lamar Jackson, Caleb Williams and Baker Mayfield
# to backups and handed their projection to the fill-in.
# Starter comes from the OFFICIAL depth chart, refreshed
# daily. Counting attempts cannot identify a starter who
# has been hurt for a month -- Chicago had Bagent ahead of
# Caleb Williams on volume while Williams is listed QB1.
cur = d[d["season"] == 2026]
QB1, _byname = {}, {}
for pid, g in cur.groupby("player_id"):
    _byname[norm(g["player_display_name"].iloc[-1])] = pid
try:
    _D = json.load(open("depth.json"))["players"]
    for k, v in _D.items():
        if v.get("pos") == "QB" and v.get("starter"):
            pid = _byname.get(k)
            if pid is not None:
                QB1[v["tm"]] = pid
    print("QB1 from depth chart: %d teams" % len(QB1))
except Exception as _e:
    print("depth chart unavailable (%s), using attempts" % _e)
for tm, g in cur.groupby("team"):
    if tm in QB1:
        continue
    tot = g.groupby("player_id")["attempts"].sum()
    if len(tot):
        QB1[tm] = tot.sort_values(ascending=False).index[0]
print("teams with an identified QB1: %d" % len(QB1))

def wmean(v, w, d0):
    w = np.asarray(w, float); v = np.asarray(v, float)
    return float((v * w).sum() / w.sum()) if w.sum() > 0 else d0

POOL = {}
for c, num, den in (("ypa", "passing_yards", "attempts"),
                    ("ptd", "passing_tds", "attempts"),
                    ("int", "passing_interceptions", "attempts"),
                    ("ypc", "rushing_yards", "carries"),
                    ("rtd", "rushing_tds", "carries")):
    POOL[c] = float(st[num].sum() / max(1.0, st[den].sum()))
POOL["att"] = float(st["attempts"].mean())
POOL["car"] = float(st["carries"].mean())
print("league QB baseline:")
for k in ("att", "ypa", "ptd", "int", "car", "ypc", "rtd"):
    print("   %-4s %8.3f" % (k, POOL[k]))

QB = {}
for pid, grp in st.groupby("player_id"):
    grp = grp.sort_values("ord")
    nm = grp["player_display_name"].iloc[-1]
    tm = grp["team"].iloc[-1]
    ago = (LASTORD - grp["ord"].values) / 100.0 * 18
    ago = np.maximum(0, np.round(ago / 1.0))
    w = 0.5 ** (np.arange(len(grp))[::-1] / HALF)
    # last season is a different team, scheme and OC.
    # THIS year is what matters -- heavy season decay.
    sy = grp["season"].values
    w = w * np.where(sy >= 2026, 1.0, 0.30)
    neff = (w.sum() ** 2) / (w ** 2).sum()

    raw = {}
    raw["att"] = wmean(grp["attempts"], w, POOL["att"])
    raw["car"] = wmean(grp["carries"], w, POOL["car"])
    pa = max(1.0, (grp["attempts"] * w).sum())
    ca = max(1.0, (grp["carries"] * w).sum())
    raw["ypa"] = (grp["passing_yards"] * w).sum() / pa
    raw["ptd"] = (grp["passing_tds"] * w).sum() / pa
    raw["int"] = (grp["passing_interceptions"] * w).sum() / pa
    raw["ypc"] = (grp["rushing_yards"] * w).sum() / ca
    raw["rtd"] = (grp["rushing_tds"] * w).sum() / ca

    sh = {}
    for k, r in REL.items():
        kk = neff * r / (1 + (neff - 1) * r) if neff > 1 else 0.0
        sh[k] = kk * raw[k] + (1 - kk) * POOL[k]
    QB[norm(nm)] = {
        "n": nm, "tm": tm, "g": int(len(grp)),
        "qb1": 1 if QB1.get(tm) == pid else 0,
        "neff": round(float(neff), 2),
        "sd_att": float(grp["attempts"].std() or 5.0),
        "sd_car": float(grp["carries"].std() or 2.0),
        **{k: float(v) for k, v in sh.items()},
        "raw_car": float(raw["car"]),
    }
json.dump(QB, open("qbparams.json", "w"), indent=0)
n1 = sum(v["qb1"] for v in QB.values())
print("\nshrunk params for %d QBs (%d starters) -> qbparams.json"
      % (len(QB), n1))
print("\nBACKUPS (will be discounted in the sim):")
for v in sorted(QB.values(), key=lambda x: x["n"]):
    if not v["qb1"]:
        print("   %-22s %s" % (v["n"][:22], v["tm"]))
for k in ("josh allen", "lamar jackson", "tyler shough",
          "bryce young", "jalen hurts", "caleb williams"):
    v = QB.get(k)
    if v:
        print("  %-18s att %5.1f ypa %4.2f ptd %.3f | "
              "car %4.1f ypc %4.2f rtd %.3f"
              % (v["n"][:18], v["att"], v["ypa"], v["ptd"],
                 v["car"], v["ypc"], v["rtd"]))
