import numpy as np, pandas as pd, json, re, os
import nflreadpy as nfl

HL, SIMS, BIAS = 3.0, 3000, 0.571
rng = np.random.default_rng(17)

def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

REL = json.load(open("reliability.json"))
PRI = json.load(open("priors.json"))
DA = json.load(open("site/_defrank.json"))["def"]
SET = json.load(open("site/_scoring.json"))
SCH = json.load(open("site/_sched.json"))["sched"]
BOARD = json.load(open("site/_board.json"))

# byes are derivable: a week missing from a team's
# schedule IS the bye. The board's bye=0 is just wrong.
import datetime
_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CURWK = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))
print("current week: %d" % CURWK)

BYE = {}
allw = set()
for t, wks in SCH.items():
    allw |= {int(w) for w in wks}
lo, hi = min(allw), max(allw)
for t, wks in SCH.items():
    have = {int(w) for w in wks}
    miss = [w for w in range(lo, hi + 1) if w not in have]
    BYE[t] = miss[0] if len(miss) == 1 else None
print("byes derived: %d teams | e.g. SEA=%s KC=%s"
      % (sum(1 for v in BYE.values() if v),
         BYE.get("SEA"), BYE.get("KC")))

S = {k: SET.get(k, 0.0) for k in
     ("rec", "rec_yd", "rec_td", "rush_yd", "rush_td",
      "pass_yd", "pass_td", "pass_int", "fum_lost")}

d = nfl.load_player_stats(seasons=[2024, 2025, 2026]).to_pandas()
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
d = d.sort_values(["player_id", "season", "week"])
BYNAME = {}
for _k, _g in d.groupby(d["player_display_name"].apply(norm)):
    BYNAME[_k] = _g
    # suffixes: "Deebo Samuel Sr." must also answer to
    # "deebo samuel", or he silently projects as zero
    for _suf in (" sr", " jr", " ii", " iii", " iv", " v"):
        if _k.endswith(_suf):
            BYNAME.setdefault(_k[:-len(_suf)], _g)

# Who is actually starting at QB right now: whoever
# took the most attempts in the team's most recent game.
# A rolling window spanning seasons cannot tell a backup
# from a starter, which is how Brady Cook ended up at 13.
QB1 = {}
_q = d[(d["att"] >= 10)]
if len(_q):
    _last = (_q.groupby(tc)[["season", "week"]]
             .apply(lambda z: sorted(
                 {(int(a2), int(b2)) for a2, b2 in
                  zip(z["season"], z["week"])})[-1]))
    for _t, _sw in _last.items():
        _g = _q[(_q[tc] == _t)
                & (_q["season"] == _sw[0])
                & (_q["week"] == _sw[1])]
        if len(_g):
            QB1[_t] = norm(_g.sort_values(
                "att", ascending=False).iloc[0]
                ["player_display_name"])
print("current starting QBs identified: %d" % len(QB1))

# A backup under centre costs the passing offence a
# measured 16% of attempts, 11% of yards per attempt and
# 29% of TD rate (460_qbinj.py, 1471 starts). Weight it
# by how likely the starter is to actually play.
QBI = json.load(open("qbinj.json"))
PLAY = {"Out": 0.0, "IR": 0.0, "PUP": 0.0, "Sus": 0.0,
        "Doubt": 0.15, "Quest": 0.75}
INJ = json.load(open("site/_inj.json"))
_byname = {}
for _v in INJ.values():
    _byname[norm(_v.get("n"))] = str(_v.get("status") or "")
QBHIT = {}
for _t, _qb in QB1.items():
    st = _byname.get(_qb, "")
    p = 1.0
    for k, v in PLAY.items():
        if st.startswith(k):
            p = v
            break
    if p < 1.0:
        QBHIT[_t] = {
            "p": p, "qb": _qb, "st": st,
            "att": p + (1 - p) * QBI["att_mult"],
            "ypa": p + (1 - p) * QBI["ypa_mult"],
            "tdr": p + (1 - p) * QBI["tdr_mult"],
        }
if QBHIT:
    print("teams with a compromised QB1:")
    for _t, _v in sorted(QBHIT.items()):
        print("   %-4s %-22s %-14s play %.0f%%  "
              "att x%.2f ypa x%.2f td x%.2f"
              % (_t, _v["qb"][:22], _v["st"], 100 * _v["p"],
                 _v["att"], _v["ypa"], _v["tdr"]))

TEAMGAMES = {}
for t, gg in d.groupby(tc):
    TEAMGAMES[t] = sorted({(int(x), int(y)) for x, y
                           in zip(gg["season"],
                                  gg["week"])})
TEAMVOL = {}
for t, g in d.groupby(tc):
    v = (g.groupby(["season", "week"])
         .agg(p=("t_tgt", "max"), r=("t_car", "max"))
         .tail(10))
    if len(v):
        w = 0.5 ** (np.arange(len(v))[::-1] / 6.0)
        TEAMVOL[t] = (float(np.sum(w * v["p"]) / w.sum()),
                      float(np.sum(w * v["r"]) / w.sum()))

def trust(ne, r1):
    return ne * r1 / (1 + (ne - 1) * r1) if ne > 0 else 0.0

def blend(g, pos):
    g = g[(g["tgt"] > 0) | (g["car"] > 0) | (g["att"] > 0)]
    n = len(g)
    if n < 2:
        return None, 0
    w = 0.5 ** (np.arange(n)[::-1] / HL)
    ne = (w.sum() ** 2) / (w ** 2).sum()
    def wa(num, den=None):
        if den is None:
            return float(np.sum(w * num) / w.sum())
        dd = float(np.sum(w * den))
        return float(np.sum(w * num) / dd) if dd > 0 else np.nan
    obs = {}
    if pos in ("WR", "TE", "RB"):
        obs["tgt_share"] = wa(np.nan_to_num(
            g["tgt"].values / np.maximum(g["t_tgt"].values, 1)))
        obs["catch_rate"] = wa(g["rec"].values, g["tgt"].values)
        obs["ypc"] = wa(g["ryd"].values, g["rec"].values)
        obs["td_per_tgt"] = wa(g["rtd"].values, g["tgt"].values)
    if pos == "RB":
        obs["car_share"] = wa(np.nan_to_num(
            g["car"].values / np.maximum(g["t_car"].values, 1)))
        obs["ypcar"] = wa(g["rush"].values, g["car"].values)
        obs["td_per_car"] = wa(g["rutd"].values, g["car"].values)
    if pos == "QB":
        obs["qb_att"] = wa(g["att"].values)
        obs["cmp_pct"] = wa(g["cmp"].values, g["att"].values)
        obs["ypa"] = wa(g["pyd"].values, g["att"].values)
        obs["td_per_att"] = wa(g["ptd"].values, g["att"].values)
        obs["int_per_att"] = wa(g["pint"].values, g["att"].values)
        obs["qb_car"] = wa(g["car"].values)
        obs["qb_rush_ypc"] = wa(g["rush"].values, g["car"].values)
    out = {}
    FALLBACK = {"td_per_tgt": 0.045, "catch_rate": 0.70,
                "ypc": 9.0, "tgt_share": 0.10,
                "td_per_car": 0.031, "ypcar": 4.29,
                "car_share": 0.30}
    for k, v in obs.items():
        p = PRI[pos].get(k, FALLBACK.get(k))
        r1 = REL[pos].get(k, 0.1)
        if p is None:
            continue
        if not np.isfinite(v):
            out[k] = p
            continue
        t = trust(ne, r1)
        out[k] = t * v + (1 - t) * p
    return out, ne

OUT, skipped = {}, 0
rows = BOARD.get("rows", [])
for r in rows:
    pos = r.get("pos")
    if pos not in ("WR", "TE", "RB", "QB"):
        continue
    team = r.get("tm")
    g = BYNAME.get(norm(r["n"]))
    if g is None or team not in SCH:
        skipped += 1
        continue
    bl, ne = blend(g, pos)
    if not bl:
        skipped += 1
        continue
    pv, rv = TEAMVOL.get(team, (30.0, 25.0))

    # Availability = of the TEAM's last 8 games, how many
    # did this player actually feature in. Measuring it
    # over the player's own games instead gives ~1.0 for
    # everyone, which is what the first attempt did.
    tg = TEAMGAMES.get(team, [])[-8:]
    if tg:
        tgs = set(tg)
        recent = g[[(int(a), int(b)) in tgs for a, b in
                    zip(g["season"], g["week"])]]
        if pos == "QB":
            played = int((recent["att"] >= 15).sum())
        else:
            played = int(((recent["tgt"]
                           + recent["car"]) >= 3).sum())
        avail = played / float(len(tg))
    else:
        avail = 1.0
    avail = max(0.15, min(1.0, avail))
    inj = str(r.get("inj") or "")
    out_wks = []
    # iterate every week, not just scheduled ones --
    # the bye is precisely the week that is missing, so
    # looping over the schedule can never emit it
    for iw in range(1, 18):
        wk = str(iw)
        if wk not in SCH[team]:
            out_wks.append({"w": iw, "o": "BYE", "m": 0.0,
                            "f": 0.0, "c": 0.0, "p20": 0.0})
            continue
        opp = SCH[team][wk].get("o")
        D = DA.get(opp, {})
        mc = D.get("m_cmp", 1.0); my = D.get("m_ypa", 1.0)
        mt = D.get("m_ptd", 1.0)
        mrc = D.get("m_ypcar", 1.0); mrt = D.get("m_rtd", 1.0)
        QH = QBHIT.get(team)
        if pos in ("WR", "TE"):
            _pv = pv * (QH["att"] if QH else 1.0)
            tg = _pv * bl.get("tgt_share", 0.10)
            rc = tg * min(.95, bl.get("catch_rate", 0.70) * mc)
            yd = rc * bl.get("ypc", 9.0) * my * (QH["ypa"] if QH else 1.0)
            td = (tg * bl.get("td_per_tgt", 0.045) * mt
                  * (QH["tdr"] if QH else 1.0))
            mean = rc * S["rec"] + yd * S["rec_yd"] + td * S["rec_td"]
            sd = max(3.0, 0.52 * mean)
        elif pos == "RB":
            ca = rv * bl.get("car_share", 0.30)
            ry = ca * bl.get("ypcar", 4.29) * mrc
            rt = ca * bl.get("td_per_car", 0.031) * mrt
            tg = pv * bl.get("tgt_share", 0.10)
            rc = tg * min(.95, bl.get("catch_rate", 0.70))
            yd = rc * bl.get("ypc", 9.0)
            td = tg * bl.get("td_per_tgt", 0.045) * mt
            mean = (ry * S["rush_yd"] + rt * S["rush_td"]
                    + rc * S["rec"] + yd * S["rec_yd"]
                    + td * S["rec_td"])
            sd = max(3.0, 0.55 * mean)
        else:
            at = bl.get("qb_att", 30.7)
            py = at * bl.get("ypa", 7.08) * my
            pt = at * bl.get("td_per_att", 0.0445) * mt
            pi = at * bl.get("int_per_att", 0.022)
            ca = bl.get("qb_car", 3.85)
            ry = ca * bl.get("qb_rush_ypc", 4.59) * mrc
            mean = (py * S["pass_yd"] + pt * S["pass_td"]
                    + pi * S["pass_int"] + ry * S["rush_yd"]
                    + 0.35 * S["rush_td"])
            sd = max(4.0, 0.38 * mean)
        mean = max(0.0, mean - (BIAS if pos in
                                ("WR", "TE") else 0))
        if pos == "QB" and QB1.get(team) != norm(r["n"]):
            mean *= 0.12    # backup: plays only on injury
        if BYE.get(team) == iw:
            mean, sd = 0.0, 0.0
        if re.match(r"^(IR|PUP|NA|Sus)", inj):
            if iw <= CURWK + 4:
                mean, sd = 0.0, 0.0
            else:
                mean *= 0.80
        elif re.match(r"^Out", inj):
            if iw <= CURWK:
                mean, sd = 0.0, 0.0
        elif re.match(r"^Doubt", inj):
            if iw <= CURWK:
                mean *= 0.35
        elif re.match(r"^Quest", inj):
            if iw <= CURWK:
                mean *= 0.88
        if sd > 0:
            sim = np.maximum(0, rng.normal(mean, sd, SIMS))
            fl, ce = float(np.percentile(sim, 10)), \
                float(np.percentile(sim, 90))
            p20 = float((sim >= 20).mean())
        else:
            fl = ce = p20 = 0.0
        out_wks.append({"w": iw, "o": opp,
                        "m": round(mean, 2),
                        "f": round(fl, 2), "c": round(ce, 2),
                        "p20": round(p20, 3)})
    played = [x["m"] for x in out_wks if x["m"] > 0]
    OUT[norm(r["n"])] = {
        "n": r["n"], "pos": pos, "tm": team,
        "bye": BYE.get(team),
        "season": round(float(np.mean(played)), 2)
        if played else 0.0,
        "avail": round(avail, 2),  # reported, not applied
        "wk": out_wks,
    }

json.dump(OUT, open("site/_projweek.json", "w"),
          separators=(",", ":"))
print("projected %d players (%d skipped), %d KB"
      % (len(OUT), skipped,
         os.path.getsize("site/_projweek.json") // 1024))

print("\n=== new vs old, top 20 by new projection ===")
old = {norm(r["n"]): r.get("live") for r in rows}
top = sorted(OUT.values(), key=lambda x: -x["season"])[:20]
print("  %-24s %-4s %7s %7s %7s"
      % ("PLAYER", "POS", "NEW", "OLD", "DIFF"))
for v in top:
    o = old.get(norm(v["n"]))
    print("  %-24s %-4s %7.1f %7s %7s"
          % (v["n"][:24], v["pos"], v["season"],
             ("%.1f" % o) if o else "-",
             ("%+.1f" % (v["season"] - o)) if o else "-"))
