import numpy as np, pandas as pd, json
import nflreadpy as nfl

HL = 3.0
R1 = {"share": 0.652, "cr": 0.067, "ypc": 0.107,
      "td": 0.010}
PPR, YD, TD = 1.0, 0.1, 6.0
MINW = 5     # need some history before we judge

d = nfl.load_player_stats(seasons=[2024, 2025]).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
for a, b in (("tgt", "targets"), ("rec", "receptions"),
             ("ryd", "receiving_yards"),
             ("rtd", "receiving_tds")):
    d[a] = d.get(b, 0)
tm = (d.groupby(["season", "week", tc])
      .agg(t_tgt=("tgt", "sum")).reset_index())
d = d.merge(tm, on=["season", "week", tc], how="left")
d = d[d["position"].isin(["WR", "TE"])].copy()
d["pts"] = (d["rec"] * PPR + d["ryd"] * YD
            + d["rtd"] * TD)
d["share"] = d["tgt"] / d["t_tgt"].replace(0, np.nan)
d = d.sort_values(["player_id", "season", "week"])

WR = d[d["position"] == "WR"]
PR = {"share": 0.16,
      "cr": WR["rec"].sum() / max(WR["tgt"].sum(), 1),
      "ypc": WR["ryd"].sum() / max(WR["rec"].sum(), 1),
      "td": WR["rtd"].sum() / max(WR["tgt"].sum(), 1)}
POSAVG = d["pts"].mean()
print("priors: %s | league avg pts %.2f"
      % ({k: round(v, 3) for k, v in PR.items()}, POSAVG))

DA = json.load(open("site/_defrank.json"))["def"]
oc = "opponent_team" if "opponent_team" in d.columns else None
print("opponent column: %s" % oc)

def trust(n_eff, r1):
    return n_eff * r1 / (1 + (n_eff - 1) * r1)

rows = []
for pid, g in d.groupby("player_id"):
    g = g.reset_index(drop=True)
    tvol = g.groupby(["season"])  # not used, per-row below
    for i in range(len(g)):
        r = g.loc[i]
        if r["season"] != 2025 or r["week"] < MINW:
            continue
        hist = g.loc[:i - 1]
        hist = hist[hist["tgt"] > 0]
        if len(hist) < 4:
            continue
        n = len(hist)
        w = 0.5 ** (np.arange(n)[::-1] / HL)
        ne = (w.sum() ** 2) / (w ** 2).sum()

        def wa(num, den=None):
            if den is None:
                return float(np.sum(w * num) / np.sum(w))
            dd = np.sum(w * den)
            return float(np.sum(w * num) / dd) if dd > 0 else 0.0

        obs = {
            "share": wa(hist["share"].fillna(0).values),
            "cr": wa(hist["rec"].values, hist["tgt"].values),
            "ypc": wa(hist["ryd"].values, hist["rec"].values),
            "td": wa(hist["rtd"].values, hist["tgt"].values),
        }
        bl = {}
        for k in obs:
            t = trust(ne, R1[k])
            bl[k] = t * obs[k] + (1 - t) * PR[k]

        # team volume from that team's recent games only
        att = float(hist["t_tgt"].tail(6).mean())
        if not np.isfinite(att) or att <= 0:
            att = 30.0

        mc = my = mt = 1.0
        if oc:
            D = DA.get(r[oc], {})
            mc = D.get("m_cmp", 1.0)
            my = D.get("m_ypa", 1.0)
            mt = D.get("m_ptd", 1.0)

        tg = att * bl["share"]
        rec = tg * min(0.95, bl["cr"] * mc)
        yds = rec * bl["ypc"] * my
        td = tg * bl["td"] * mt
        model = rec * PPR + yds * YD + td * TD

        last3 = float(hist["pts"].tail(3).mean())
        std = float(hist["pts"].mean())
        rows.append({"pid": pid, "wk": int(r["week"]),
                     "act": float(r["pts"]),
                     "model": model, "last3": last3,
                     "std": std, "flat": POSAVG})

R = pd.DataFrame(rows)
print("\nplayer-weeks scored: %d" % len(R))
print("\n%-18s %8s %8s %8s"
      % ("METHOD", "MAE", "BIAS", "R"))
for c, lbl in (("model", "our model"),
               ("last3", "last 3 games"),
               ("std", "season to date"),
               ("flat", "position average")):
    e = R[c] - R["act"]
    r = np.corrcoef(R[c], R["act"])[0, 1]
    print("%-18s %8.3f %8.3f %8.3f"
          % (lbl, e.abs().mean(), e.mean(), r))

print("\nby volume of player (season-to-date avg pts):")
R["band"] = pd.cut(R["std"], [0, 6, 10, 14, 99],
                   labels=["<6", "6-10", "10-14", "14+"])
for b, s in R.groupby("band", observed=True):
    print("  %-6s n=%-5d model %.2f   last3 %.2f   std %.2f"
          % (b, len(s), (s["model"] - s["act"]).abs().mean(),
             (s["last3"] - s["act"]).abs().mean(),
             (s["std"] - s["act"]).abs().mean()))
