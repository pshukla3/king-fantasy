import json
import nflreadpy as nfl
from namekey import nk, tfix

B = ["0_19", "20_29", "30_39", "40_49", "50_59", "60_"]
KPTS = {"0_19": 3, "20_29": 3, "30_39": 3, "40_49": 4,
        "50_59": 5, "60_": 5}
try:
    MINE = json.load(open("league_scoring.json"))
except Exception:
    MINE = {}

d = nfl.load_player_stats([2026]).to_pandas()
need = ["passing_yards", "passing_tds", "passing_interceptions",
        "rushing_yards", "rushing_tds", "receptions",
        "receiving_yards", "receiving_tds", "fg_att",
        "fg_made", "pat_made", "pat_att",
        "rushing_fumbles_lost", "receiving_fumbles_lost",
        "sack_fumbles_lost"]
need += ["fg_made_" + b for b in B] + ["fg_missed_" + b for b in B]
for c in need:
    if c not in d.columns:
        d[c] = 0.0
    d[c] = d[c].fillna(0.0).astype(float)

def ppr(r):
    return (r["passing_yards"] * .04 + r["passing_tds"] * 4
            - r["passing_interceptions"]
            + r["rushing_yards"] * .1 + r["rushing_tds"] * 6
            + r["receptions"] + r["receiving_yards"] * .1
            + r["receiving_tds"] * 6
            - (r["rushing_fumbles_lost"]
               + r["receiving_fumbles_lost"]
               + r["sack_fumbles_lost"]) * 2)

def kick(r, S=None):
    t = 0.0
    for b in B:
        if S:
            k = "fgm_50p" if b in ("50_59", "60_") else "fgm_" + b
            pts = S.get(k, S.get("fgm_" + b, 3))
            miss = S.get("fgmiss", -1)
        else:
            pts, miss = KPTS[b], -1
        t += r["fg_made_" + b] * pts
        t += r["fg_missed_" + b] * miss
    xm = S.get("xpm", 1) if S else 1
    xmiss = S.get("xpmiss", 0) if S else 0
    return t + r["pat_made"] * xm \
        + (r["pat_att"] - r["pat_made"]) * xmiss

d = d[d["position"].isin(["QB", "RB", "WR", "TE", "K"])]
d["pts"] = d.apply(
    lambda r: kick(r) if r["position"] == "K" else ppr(r),
    axis=1)
d["pts_lg"] = d.apply(
    lambda r: kick(r, MINE) if r["position"] == "K" else ppr(r),
    axis=1)
d = d[(d["pts"] != 0) | (d["pts_lg"] != 0)]

try:
    IDS = json.load(open("site/_ids.json"))["canon"]
except Exception:
    IDS = {}
BRD = {}
try:
    for r in json.load(open("site/_board.json"))["rows"]:
        if r.get("pid"):
            BRD[r["pid"]] = r
except Exception:
    pass

WK = {}
for w, g in d.groupby("week"):
    rows = []
    for _, r in g.sort_values("pts", ascending=False).iterrows():
        pid = r.get("player_id")
        b = BRD.get(pid, {})
        rows.append({
            "n": r["player_display_name"],
            "pos": r["position"], "tm": tfix(r["team"]),
            "p": round(float(r["pts"]), 1),
            "pl": round(float(r["pts_lg"]), 1),
            "pid": pid, "img": b.get("img") or "",
            "proj": b.get("live"),
            "ry": int(r["rushing_yards"]),
            "rt": int(r["rushing_tds"]),
            "re": int(r["receptions"]),
            "cy": int(r["receiving_yards"]),
            "ct": int(r["receiving_tds"]),
            "py": int(r["passing_yards"]),
            "pt": int(r["passing_tds"]),
            "fm": int(r["fg_made"]), "fa": int(r["fg_att"]),
        })
    WK[str(int(w))] = rows[:120]

last = max(int(k) for k in WK)
json.dump({"weeks": sorted(WK, key=int), "last": last,
           "by_week": WK},
          open("site/_topwk.json", "w"),
          separators=(",", ":"))
print("wrote site/_topwk.json  weeks %s"
      % sorted(WK, key=int))

print("\n=== TOP 15, WEEK %d (default scoring) ===" % last)
print("  %-3s %-24s %-4s %-4s %7s %8s"
      % ("#", "PLAYER", "POS", "TM", "PTS", "PROJ"))
for i, r in enumerate(WK[str(last)][:15], 1):
    print("  %-3d %-24s %-4s %-4s %7.1f %8s"
          % (i, r["n"][:24], r["pos"], r["tm"], r["p"],
             ("%.1f" % r["proj"]) if r["proj"] else "-"))
for pos in ("QB", "RB", "WR", "TE", "K"):
    top = [r for r in WK[str(last)] if r["pos"] == pos][:3]
    print("\n  %s: %s" % (pos, ", ".join(
        "%s %.1f" % (t["n"].split()[-1], t["p"]) for t in top)))
