import pandas as pd

B = pd.read_csv("board_final.csv", low_memory=False)
SET = {"Fernando Mendoza": 1, "Ty Simpson": 2,
       "Trevor Siemian": 3, "Carson Beck": 3,
       "Drew Allar": 3, "Kirk Cousins": 2}
n = 0
for nm, d in SET.items():
    m = ((B["position"] == "QB")
         & (B["player_display_name"].astype(str) == nm))
    if m.sum():
        B.loc[m, "depth_rank"] = d
        n += int(m.sum())
    else:
        print("  MISSING: %s" % nm)

RK = pd.read_csv("rookie_qb_seasons.csv")
R5 = RK[RK["pick"] <= 5]
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
att, ypa = 30.3, float(R5["ypa"].mean())
tdr = float(R5["tdr"].mean())
ry = float(R5["ryd"].sum() / R5["g"].sum())
rt = float(R5["rtd"].sum() / R5["g"].sum())
mp = (att * ypa * float(V["pass_yd"])
      + att * tdr * float(V["pass_td"])
      + att * 0.0211 * float(V["pass_int"])
      + ry * float(V["rush_yd"])
      + rt * float(V["rush_td"]))
m = (B["player_display_name"].astype(str)
     .str.contains("Mendoza", na=False))
if m.sum():
    B.loc[m, "points"] = mp
    B.loc[m, "team"] = "LV"
    print("Mendoza -> QB1 LV %.2f ppg (rookie prior)" % mp)

B.to_csv("board_final.csv", index=False)
Q = B[B["position"] == "QB"]
have = set(str(t) for t in
           Q.loc[Q["depth_rank"] == 1, "team"].dropna())
LONG = {"SFO":"SF","GBP":"GB","NEP":"NE","NOS":"NO",
        "TAM":"TB","KCC":"KC","LVR":"LV","JAC":"JAX",
        "ARZ":"ARI","BLT":"BAL","CLV":"CLE","HST":"HOU",
        "LAR":"LA"}
best = {}
try:
    import nflreadpy as _nfl
    _d = _nfl.load_player_stats(seasons=[2026])
    acc = {}
    for _r in _d.iter_rows(named=True):
        if (_r.get("position") or "") != "QB":
            continue
        _t = _r.get("team")
        if not _t:
            continue
        _t = LONG.get(str(_t).upper(), str(_t).upper())
        _k = (_t, _r.get("player_display_name"))
        acc[_k] = acc.get(_k, 0) + (_r.get("attempts") or 0)
    for (_t, _nm), _a in acc.items():
        if _a > best.get(_t, (0, None))[0]:
            best[_t] = (_a, _nm)
except Exception as _e:
    print("  attempts lookup failed: %s" % _e)

allt = set(str(t) for t in Q["team"].dropna().unique())
filled = 0
for t in sorted(allt - have):
    cand = best.get(t, (0, None))[1]
    m = ((B["position"] == "QB") & (B["team"] == t)
         & (B["player_display_name"].astype(str) == str(cand)))
    if not m.sum():
        sub = B[(B["position"] == "QB") & (B["team"] == t)]
        if not len(sub):
            continue
        idx = sub["points"].astype(float).idxmax()
        m = B.index == idx
        cand = B.loc[idx, "player_display_name"]
    B.loc[m, "depth_rank"] = 1
    filled += 1
    print("  QB1 filled: %-4s -> %s" % (t, cand))

B.to_csv("board_final.csv", index=False)
Q = B[B["position"] == "QB"]
got = int((Q["depth_rank"] == 1).sum())
print("depth set %d | starters %d | filled %d | unranked %d"
      % (n, got, filled, int(Q["depth_rank"].isna().sum())))
if got < 30:
    raise SystemExit("only %d starting QBs -- depth data bad" % got)
if got != 32:
    print("  WARN: %d QB1s, expected 32" % got)
print("OK")
