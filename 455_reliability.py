import numpy as np, pandas as pd, json
import nflreadpy as nfl

d = nfl.load_player_stats(seasons=[2023, 2024, 2025, 2026]
                          ).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
M = {"tgt": "targets", "rec": "receptions",
     "ryd": "receiving_yards", "rtd": "receiving_tds",
     "car": "carries", "rush": "rushing_yards",
     "rutd": "rushing_tds", "att": "attempts",
     "cmp": "completions", "pyd": "passing_yards",
     "ptd": "passing_tds", "pint": "passing_interceptions"}
for a, b in M.items():
    d[a] = d.get(b, 0)
tm = (d.groupby(["season", "week", tc])
      .agg(t_tgt=("tgt", "sum"), t_car=("car", "sum"))
      .reset_index())
d = d.merge(tm, on=["season", "week", tc], how="left")

def safe(a, b):
    return np.where(b > 0, a / np.maximum(b, 1e-9), np.nan)

d["tgt_share"] = safe(d["tgt"], d["t_tgt"])
d["car_share"] = safe(d["car"], d["t_car"])
d["catch_rate"] = safe(d["rec"], d["tgt"])
d["ypc"] = safe(d["ryd"], d["rec"])
d["td_per_tgt"] = safe(d["rtd"], d["tgt"])
d["ypcar"] = safe(d["rush"], d["car"])
d["td_per_car"] = safe(d["rutd"], d["car"])
d["cmp_pct"] = safe(d["cmp"], d["att"])
d["ypa"] = safe(d["pyd"], d["att"])
d["td_per_att"] = safe(d["ptd"], d["att"])
d["int_per_att"] = safe(d["pint"], d["att"])
d["qb_att"] = np.where(d["att"] > 0, d["att"], np.nan)
d["qb_car"] = np.where(d["att"] > 0, d["car"], np.nan)
d["qb_rush_ypc"] = np.where(d["att"] > 0,
                            safe(d["rush"], d["car"]), np.nan)

SPEC = {
    "WR": ["tgt_share", "catch_rate", "ypc", "td_per_tgt"],
    "TE": ["tgt_share", "catch_rate", "ypc", "td_per_tgt"],
    "RB": ["car_share", "ypcar", "td_per_car",
           "tgt_share", "catch_rate", "ypc"],
    "QB": ["qb_att", "cmp_pct", "ypa", "td_per_att",
           "int_per_att", "qb_car", "qb_rush_ypc"],
}

d = d.sort_values(["player_id", "season", "week"])
OUT = {}
print("week-to-week reliability of each component")
print("  (how much one game tells you about the next)\n")
print("  %-4s %-14s %8s %8s  %s"
      % ("POS", "COMPONENT", "N", "r", "meaning"))
for pos, comps in SPEC.items():
    OUT[pos] = {}
    for c in comps:
        s = d[(d["position"] == pos) & d[c].notna()].copy()
        s["prev"] = s.groupby(["player_id", "season"])[c].shift(1)
        s = s.dropna(subset=["prev"])
        if len(s) < 200:
            print("  %-4s %-14s %8d   too few" % (pos, c, len(s)))
            continue
        r = float(np.corrcoef(s[c], s["prev"])[0, 1])
        r = max(0.0, min(0.95, r))
        OUT[pos][c] = round(r, 4)
        mean = ("opportunity" if r >= .40 else
                ("part signal" if r >= .15 else "mostly noise"))
        print("  %-4s %-14s %8d %8.3f  %s"
              % (pos, c, len(s), r, mean))

json.dump(OUT, open("reliability.json", "w"), indent=1)
print("\nwrote reliability.json")

print("\n=== position priors (league rates) ===")
PR = {}
for pos in SPEC:
    s = d[d["position"] == pos]
    p = {}
    if pos in ("WR", "TE"):
        p["tgt_share"] = 0.16 if pos == "WR" else 0.13
        p["catch_rate"] = float(s["rec"].sum()
                                / max(s["tgt"].sum(), 1))
        p["ypc"] = float(s["ryd"].sum()
                         / max(s["rec"].sum(), 1))
        p["td_per_tgt"] = float(s["rtd"].sum()
                                / max(s["tgt"].sum(), 1))
    elif pos == "RB":
        p["car_share"] = 0.35
        p["ypcar"] = float(s["rush"].sum()
                           / max(s["car"].sum(), 1))
        p["td_per_car"] = float(s["rutd"].sum()
                                / max(s["car"].sum(), 1))
        p["tgt_share"] = 0.09
        p["catch_rate"] = float(s["rec"].sum()
                                / max(s["tgt"].sum(), 1))
        p["ypc"] = float(s["ryd"].sum()
                         / max(s["rec"].sum(), 1))
    else:
        q = s[s["att"] > 5]
        p["qb_att"] = float(q["att"].mean())
        p["cmp_pct"] = float(q["cmp"].sum()
                             / max(q["att"].sum(), 1))
        p["ypa"] = float(q["pyd"].sum()
                         / max(q["att"].sum(), 1))
        p["td_per_att"] = float(q["ptd"].sum()
                                / max(q["att"].sum(), 1))
        p["int_per_att"] = float(q["pint"].sum()
                                 / max(q["att"].sum(), 1))
        p["qb_car"] = float(q["car"].mean())
        p["qb_rush_ypc"] = float(q["rush"].sum()
                                 / max(q["car"].sum(), 1))
    PR[pos] = {k: round(v, 4) for k, v in p.items()}
    print("  %-4s %s" % (pos, PR[pos]))
json.dump(PR, open("priors.json", "w"), indent=1)
print("\nwrote priors.json")
