import numpy as np, pandas as pd, json, re
import nflreadpy as nfl

NAME = "Jaxon Smith-Njigba"
TEAM = "SEA"
SIMS = 20000
rng = np.random.default_rng(7)

def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# measured week-to-week reliability (448_components.py)
R1 = {"tgt_share": 0.652, "catch_rate": 0.067,
      "ypc": 0.107, "td_per_tgt": 0.010}

def weight(n, r1):
    """Spearman-Brown: how much to trust n games of this."""
    if n <= 0: return 0.0
    return n * r1 / (1 + (n - 1) * r1)

d = nfl.load_player_stats(seasons=[2024, 2025, 2026]).to_pandas()
tcol = "team" if "team" in d.columns else "recent_team"
d["tgt"] = d.get("targets", 0); d["rec"] = d.get("receptions", 0)
d["ryd"] = d.get("receiving_yards", 0)
d["rtd"] = d.get("receiving_tds", 0)
tm = (d.groupby(["season", "week", tcol])
      .agg(t_tgt=("tgt", "sum")).reset_index())
d = d.merge(tm, on=["season", "week", tcol], how="left")

WR = d[d["position"] == "WR"]
PRIOR = {
    "catch_rate": (WR["rec"].sum() / max(WR["tgt"].sum(), 1)),
    "ypc": (WR["ryd"].sum() / max(WR["rec"].sum(), 1)),
    "td_per_tgt": (WR["rtd"].sum() / max(WR["tgt"].sum(), 1)),
}
print("league WR priors: catch %.3f  ypc %.2f  td/tgt %.4f"
      % (PRIOR["catch_rate"], PRIOR["ypc"],
         PRIOR["td_per_tgt"]))

me = d[d["player_display_name"].apply(norm) == norm(NAME)]
me = me[me["tgt"] > 0].sort_values(["season", "week"])
print("\n%s: %d games with targets" % (NAME, len(me)))

obs = {
    "tgt_share": (me["tgt"] / me["t_tgt"]).mean(),
    "catch_rate": me["rec"].sum() / max(me["tgt"].sum(), 1),
    "ypc": me["ryd"].sum() / max(me["rec"].sum(), 1),
    "td_per_tgt": me["rtd"].sum() / max(me["tgt"].sum(), 1),
}
n = len(me)
PRIOR["tgt_share"] = 0.16
BLEND = {}
print("\n%-12s %8s %8s %7s %9s"
      % ("COMPONENT", "HIS", "PRIOR", "WEIGHT", "USED"))
for c in ("tgt_share", "catch_rate", "ypc", "td_per_tgt"):
    w = weight(n, R1[c])
    v = w * obs[c] + (1 - w) * PRIOR[c]
    BLEND[c] = v
    print("%-12s %8.3f %8.3f %7.2f %9.3f"
          % (c, obs[c], PRIOR[c], w, v))

# spread of his own game-to-game share
shares = (me["tgt"] / me["t_tgt"]).values
SH_SD = max(0.03, np.std(shares))
team_att = d[(d[tcol] == TEAM)].groupby(
    ["season", "week"])["tgt"].sum()
ATT_MU, ATT_SD = team_att.mean(), max(3.0, team_att.std())
print("\n%s team targets/game: %.1f +/- %.1f"
      % (TEAM, ATT_MU, ATT_SD))

# opponent: pass attempts faced and catch rate allowed
opp = d.copy()
if "opponent_team" in opp.columns:
    ocol = "opponent_team"
else:
    ocol = None
DEF = {}
if ocol:
    gg = (opp.groupby([ocol, "season", "week"])
          .agg(att=("tgt", "sum"), rec=("rec", "sum"),
               yds=("ryd", "sum"), td=("rtd", "sum"))
          .reset_index())
    lg_att = gg["att"].mean()
    lg_ypc = gg["yds"].sum() / max(gg["rec"].sum(), 1)
    for t, s in gg.groupby(ocol):
        DEF[t] = {
            "att_mult": s["att"].mean() / lg_att,
            "ypc_mult": ((s["yds"].sum() / max(s["rec"].sum(), 1))
                         / lg_ypc),
        }
    print("league avg pass attempts faced: %.1f" % lg_att)

SCH = json.load(open("site/_sched.json"))["sched"].get(TEAM, {})
SET = json.load(open("site/_scoring.json"))
PPR = SET.get("rec", 1.0); YD = SET.get("rec_yd", 0.1)
TD = SET.get("rec_td", 6.0)

print("\n=== WEEKLY PROJECTION (%d sims each) ===" % SIMS)
print("  %-4s %-6s %7s %7s %7s %7s %7s"
      % ("WK", "OPP", "MEAN", "FLOOR", "CEIL", "P20+", "P<8"))
out = []
for w in sorted(SCH, key=lambda x: int(x)):
    if int(w) < 2 or int(w) > 17:
        continue
    o = SCH[w].get("o")
    dm = DEF.get(o, {"att_mult": 1.0, "ypc_mult": 1.0})
    att = rng.normal(ATT_MU * dm["att_mult"], ATT_SD, SIMS)
    att = np.clip(att, 10, 60)
    sh = np.clip(rng.normal(BLEND["tgt_share"], SH_SD, SIMS),
                 0.02, 0.60)
    tgts = np.maximum(0, np.round(att * sh))
    recs = rng.binomial(tgts.astype(int),
                        np.clip(BLEND["catch_rate"], .05, .95))
    ypc = rng.normal(BLEND["ypc"] * dm["ypc_mult"], 3.2, SIMS)
    yards = np.maximum(0, recs * ypc)
    tds = rng.poisson(np.maximum(0, tgts * BLEND["td_per_tgt"]))
    pts = recs * PPR + yards * YD + tds * TD
    out.append({
        "wk": int(w), "opp": o,
        "mean": float(pts.mean()),
        "floor": float(np.percentile(pts, 10)),
        "ceil": float(np.percentile(pts, 90)),
        "p20": float((pts >= 20).mean()),
        "p8": float((pts < 8).mean()),
    })
    print("  %-4s %-6s %7.1f %7.1f %7.1f %6.0f%% %6.0f%%"
          % (w, o, out[-1]["mean"], out[-1]["floor"],
             out[-1]["ceil"], 100 * out[-1]["p20"],
             100 * out[-1]["p8"]))

m = np.mean([x["mean"] for x in out])
print("\n  season average of weekly means: %.1f" % m)
print("  current board projection:        18.4")
print("  his actual 21-game average:      20.7")
json.dump(out, open("site/_agent_jsn.json", "w"),
          separators=(",", ":"))
print("\nwrote site/_agent_jsn.json")
