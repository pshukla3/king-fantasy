import numpy as np, json, re, sys
import nflreadpy as nfl

NAME = " ".join(sys.argv[1:]) or "Jaxon Smith-Njigba"
SIMS, HL = 20000, 3.0
R1 = {"tgt_share": 0.652, "catch_rate": 0.067,
      "ypc": 0.107, "td_per_tgt": 0.010}
rng = np.random.default_rng(11)

def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

K = norm(NAME)
B = json.load(open("site/_board.json"))["rows"]
row = next((r for r in B if norm(r["n"]) == K), None)
TEAM = row["tm"]
DA = json.load(open("site/_defrank.json"))
SET = json.load(open("site/_scoring.json"))
SCH = json.load(open("site/_sched.json"))["sched"].get(TEAM, {})

d = nfl.load_player_stats(seasons=[2024, 2025, 2026]).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
for a, b in (("tgt", "targets"), ("rec", "receptions"),
             ("ryd", "receiving_yards"),
             ("rtd", "receiving_tds")):
    d[a] = d.get(b, 0)
tm = (d.groupby(["season", "week", tc])
      .agg(t_tgt=("tgt", "sum")).reset_index())
d = d.merge(tm, on=["season", "week", tc], how="left")

WR = d[d["position"] == "WR"]
PRIOR = {"tgt_share": 0.16,
         "catch_rate": WR["rec"].sum() / max(WR["tgt"].sum(), 1),
         "ypc": WR["ryd"].sum() / max(WR["rec"].sum(), 1),
         "td_per_tgt": WR["rtd"].sum() / max(WR["tgt"].sum(), 1)}

me = d[d["player_display_name"].apply(norm) == K]
me = me[me["tgt"] > 0].sort_values(["season", "week"])
n = len(me)
ago = np.arange(n)[::-1]
w = 0.5 ** (ago / HL)          # half-life 3, measured
n_eff = (w.sum() ** 2) / (w ** 2).sum()

def wavg(num, den=None):
    if den is None:
        return float(np.sum(w * num) / np.sum(w))
    return float(np.sum(w * num) / max(np.sum(w * den), 1e-9))

obs = {
    "tgt_share": wavg(me["tgt"].values / me["t_tgt"].values),
    "catch_rate": wavg(me["rec"].values, me["tgt"].values),
    "ypc": wavg(me["ryd"].values, me["rec"].values),
    "td_per_tgt": wavg(me["rtd"].values, me["tgt"].values),
}
print("=" * 58)
print("AGENT: %s  (%s %s)" % (row["n"], row["pos"], TEAM))
print("=" * 58)
print("games %d, effective sample after recency %.1f" % (n, n_eff))
print("\n%-12s %8s %8s %7s %9s"
      % ("COMPONENT", "RECENT", "PRIOR", "TRUST", "USED"))
BL = {}
for c in R1:
    tw = n_eff * R1[c] / (1 + (n_eff - 1) * R1[c])
    BL[c] = tw * obs[c] + (1 - tw) * PRIOR[c]
    print("%-12s %8.3f %8.3f %7.2f %9.3f"
          % (c, obs[c], PRIOR[c], tw, BL[c]))

sh = me["tgt"].values / me["t_tgt"].values
SH_SD = max(0.035, float(np.sqrt(
    np.sum(w * (sh - obs["tgt_share"]) ** 2) / np.sum(w))))

ta = d[d[tc] == TEAM].groupby(["season", "week"])["tgt"].sum()
ta = ta.values[-12:]
aw = 0.5 ** (np.arange(len(ta))[::-1] / 6.0)
ATT = float(np.sum(aw * ta) / np.sum(aw))
ATT_SD = max(3.5, float(np.std(ta)))
print("\n%s pass volume %.1f +/- %.1f   share sd %.3f"
      % (TEAM, ATT, ATT_SD, SH_SD))

PPR = SET.get("rec", 1.0); YD = SET.get("rec_yd", .1)
TD = SET.get("rec_td", 6.0)
BYE = row.get("bye") or 0

print("\n=== WEEKLY PROJECTION ===")
print("  %-4s %-5s %6s %6s %6s %6s %6s  %s"
      % ("WK", "OPP", "MEAN", "FLOOR", "CEIL", "P20+",
         "P<8", "MATCHUP"))
out = []
for wk in sorted(SCH, key=lambda x: int(x)):
    iw = int(wk)
    if iw < 2 or iw > 17:
        continue
    o = SCH[wk].get("o")
    if BYE and iw == BYE:
        out.append({"wk": iw, "opp": "BYE", "mean": 0.0,
                    "floor": 0.0, "ceil": 0.0, "p20": 0.0})
        print("  %-4s %-5s %6.1f %6.1f %6.1f %5.0f%% %5.0f%%"
              "  bye week" % (wk, "BYE", 0, 0, 0, 0, 100))
        continue
    D = DA["def"].get(o, {})
    ma = 1.0                       # volume: game script
    mc = D.get("m_cmp", 1.0)       # catch rate allowed
    my = D.get("m_ypa", 1.0)       # yards per attempt
    mt = D.get("m_ptd", 1.0)       # TD rate allowed
    prk = D.get("pass_rank", 16)

    att = np.clip(rng.normal(ATT * ma, ATT_SD, SIMS), 12, 55)
    s = np.clip(rng.normal(BL["tgt_share"], SH_SD, SIMS),
                .02, .60)
    tg = np.maximum(0, np.round(att * s)).astype(int)
    rec = rng.binomial(tg, np.clip(BL["catch_rate"] * mc,
                                   .05, .95))
    ypc = np.maximum(0, rng.normal(BL["ypc"] * my, 3.4, SIMS))
    yd = rec * ypc
    td = rng.poisson(np.maximum(0, tg * BL["td_per_tgt"] * mt))
    pts = rec * PPR + yd * YD + td * TD

    tag = ("#%d pass D" % prk) if prk else "-"
    r = {"wk": iw, "opp": o, "mean": float(pts.mean()),
         "floor": float(np.percentile(pts, 10)),
         "ceil": float(np.percentile(pts, 90)),
         "p20": float((pts >= 20).mean()),
         "p8": float((pts < 8).mean()),
         "tag": tag, "ypc_mult": my, "td_mult": mt}
    out.append(r)
    print("  %-4s %-5s %6.1f %6.1f %6.1f %5.0f%% %5.0f%%"
          "  %s (ypa %.2f, td %.2f)"
          % (wk, o, r["mean"], r["floor"], r["ceil"],
             100 * r["p20"], 100 * r["p8"], tag, my, mt))

ms = [x["mean"] for x in out if x["opp"] != "BYE"]
print("\n  weekly range %.1f to %.1f  (spread %.1f)"
      % (min(ms), max(ms), max(ms) - min(ms)))
print("  season average %.1f" % np.mean(ms))
print("  old board projection 18.4 | his 21-game avg 20.7")
json.dump(out, open("site/_agent_%s.json" % K.replace(" ", "_"),
                    "w"), separators=(",", ":"))
print("\nwrote site/_agent_%s.json" % K.replace(" ", "_"))
