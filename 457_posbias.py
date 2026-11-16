import numpy as np, pandas as pd, json, re
import nflreadpy as nfl

HL = 3.0
REL = json.load(open("reliability.json"))
PRI = json.load(open("priors.json"))
SET = json.load(open("site/_scoring.json"))
S = {k: SET.get(k, 0.0) for k in
     ("rec", "rec_yd", "rec_td", "rush_yd", "rush_td",
      "pass_yd", "pass_td", "pass_int")}

d = nfl.load_player_stats(seasons=[2024, 2025]).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
M = {"tgt": "targets", "rec": "receptions",
     "ryd": "receiving_yards", "rtd": "receiving_tds",
     "car": "carries", "rush": "rushing_yards",
     "rutd": "rushing_tds", "att": "attempts",
     "cmp": "completions", "pyd": "passing_yards",
     "ptd": "passing_tds", "pint": "passing_interceptions"}
for a, b in M.items():
    d[a] = d.get(b, 0)
tv = (d.groupby(["season", "week", tc])
      .agg(t_tgt=("tgt", "sum"), t_car=("car", "sum"))
      .reset_index())
d = d.merge(tv, on=["season", "week", tc], how="left")
d["pts"] = (d["rec"] * S["rec"] + d["ryd"] * S["rec_yd"]
            + d["rtd"] * S["rec_td"]
            + d["rush"] * S["rush_yd"]
            + d["rutd"] * S["rush_td"]
            + d["pyd"] * S["pass_yd"]
            + d["ptd"] * S["pass_td"]
            + d["pint"] * S["pass_int"])
d = d.sort_values(["player_id", "season", "week"])

def trust(ne, r1):
    return ne * r1 / (1 + (ne - 1) * r1) if ne > 0 else 0.0

rows = []
for pos in ("QB", "RB", "WR", "TE"):
    sub = d[d["position"] == pos]
    for pid, g in sub.groupby("player_id"):
        g = g.reset_index(drop=True)
        for i in range(len(g)):
            r = g.loc[i]
            if r["season"] != 2025 or r["week"] < 5:
                continue
            if pos == "QB" and r["att"] < 10:
                continue
            if pos != "QB" and (r["tgt"] + r["car"]) < 2:
                continue
            h = g.loc[:i - 1]
            h = h[(h["att"] >= 10) if pos == "QB"
                  else ((h["tgt"] + h["car"]) >= 2)]
            if len(h) < 4:
                continue
            n = len(h)
            w = 0.5 ** (np.arange(n)[::-1] / HL)
            ne = (w.sum() ** 2) / (w ** 2).sum()

            def wa(num, den=None):
                if den is None:
                    return float(np.sum(w * num) / w.sum())
                dd = float(np.sum(w * den))
                return (float(np.sum(w * num) / dd)
                        if dd > 0 else np.nan)

            def bl(key, num, den=None):
                v = wa(num, den)
                p = PRI[pos].get(key, 0.0)
                if not np.isfinite(v):
                    return p
                t = trust(ne, REL[pos].get(key, 0.1))
                return t * v + (1 - t) * p

            pv = float(h["t_tgt"].tail(6).mean() or 30)
            rv = float(h["t_car"].tail(6).mean() or 25)
            if pos == "QB":
                at = bl("qb_att", h["att"].values)
                ypa = bl("ypa", h["pyd"].values, h["att"].values)
                tda = bl("td_per_att", h["ptd"].values,
                         h["att"].values)
                ia = bl("int_per_att", h["pint"].values,
                        h["att"].values)
                ca = bl("qb_car", h["car"].values)
                ry = bl("qb_rush_ypc", h["rush"].values,
                        h["car"].values)
                m = (at * ypa * S["pass_yd"]
                     + at * tda * S["pass_td"]
                     + at * ia * S["pass_int"]
                     + ca * ry * S["rush_yd"]
                     + 0.35 * S["rush_td"])
            elif pos == "RB":
                cs = bl("car_share", np.nan_to_num(
                    h["car"].values / np.maximum(
                        h["t_car"].values, 1)))
                yc = bl("ypcar", h["rush"].values,
                        h["car"].values)
                tc2 = bl("td_per_car", h["rutd"].values,
                         h["car"].values)
                ts = bl("tgt_share", np.nan_to_num(
                    h["tgt"].values / np.maximum(
                        h["t_tgt"].values, 1)))
                cr = bl("catch_rate", h["rec"].values,
                        h["tgt"].values)
                yp = bl("ypc", h["ryd"].values, h["rec"].values)
                ca = rv * cs
                tg = pv * ts
                m = (ca * yc * S["rush_yd"]
                     + ca * tc2 * S["rush_td"]
                     + tg * cr * S["rec"]
                     + tg * cr * yp * S["rec_yd"]
                     + tg * 0.045 * S["rec_td"])
            else:
                ts = bl("tgt_share", np.nan_to_num(
                    h["tgt"].values / np.maximum(
                        h["t_tgt"].values, 1)))
                cr = bl("catch_rate", h["rec"].values,
                        h["tgt"].values)
                yp = bl("ypc", h["ryd"].values, h["rec"].values)
                td = bl("td_per_tgt", h["rtd"].values,
                        h["tgt"].values)
                tg = pv * ts
                m = (tg * cr * S["rec"]
                     + tg * cr * yp * S["rec_yd"]
                     + tg * td * S["rec_td"])
            rows.append({"pos": pos, "proj": m,
                         "act": float(r["pts"])})

R = pd.DataFrame(rows)
print("=== bias by position (2025 walk-forward) ===")
print("  %-4s %7s %9s %9s %9s"
      % ("POS", "N", "MEAN PROJ", "MEAN ACT", "BIAS"))
for pos, s in R.groupby("pos"):
    e = s["proj"] - s["act"]
    print("  %-4s %7d %9.2f %9.2f %+9.3f"
          % (pos, len(s), s["proj"].mean(),
             s["act"].mean(), e.mean()))
    print("       MAE %.3f   correlation %.3f"
          % (e.abs().mean(),
             np.corrcoef(s["proj"], s["act"])[0, 1]))
json.dump({p: float((g["proj"] - g["act"]).mean())
           for p, g in R.groupby("pos")},
          open("posbias.json", "w"), indent=1)
print("\nwrote posbias.json")
