import pandas as pd

ALIAS = {"LAR": "LA", "JAC": "JAX", "WSH": "WAS", "ARZ": "ARI", "CLV": "CLE"}
def fix(x):
    return ALIAS.get(str(x), str(x))

def grab(fn, **kw):
    try:
        import nflreadpy as nfl
        r = getattr(nfl, fn)(**kw)
        return r.to_pandas() if hasattr(r, "to_pandas") else pd.DataFrame(r)
    except Exception as e:
        print("  %s failed: %s" % (fn, e))
        return None

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
OC, PC = "opponent_team", "fantasy_points_ppr"
H[OC] = H[OC].map(fix)

def prof(season, pos="RB"):
    d = H[(H["season"] == season) & H[OC].notna()]
    gm = d.groupby(OC)["week"].nunique()
    v = d[d["position"] == pos].groupby(OC)[PC].sum()
    return v / gm

p24, p25 = prof(2024, "WR"), prof(2025, "WR")
j = pd.concat([p24.rename("y24"), p25.rename("y25")], axis=1).dropna()
print("=" * 70)
print("VALIDATION: does last year's RB defense predict this year's?")
print("=" * 70)
print("  n = %d teams      r = %.3f" % (len(j), j["y24"].corr(j["y25"])))
print("  2025 fpWR allowed: %.1f (best D) to %.1f (worst D), league avg %.1f"
      % (p25.min(), p25.max(), p25.mean()))
print("  full spread = %.1f pts/gm between the very best and worst matchup"
      % (p25.max() - p25.min()))

sh = grab("load_schedules", seasons=[2023, 2024, 2025])
if sh is not None:
    rows = []
    for _, r in sh.iterrows():
        rows.append((r["season"], r["week"], fix(r["home_team"]), 1))
        rows.append((r["season"], r["week"], fix(r["away_team"]), 0))
    HA = pd.DataFrame(rows, columns=["season", "week", "tm_", "home"])
    tc = "team" if "team" in H.columns else "recent_team"
    rb = H[(H["position"] == "RB") & H["season"].isin([2023, 2024, 2025])].copy()
    rb["tm_"] = rb[tc].map(fix)
    rb = rb.merge(HA, on=["season", "week", "tm_"], how="inner")
    hm, aw = rb[rb["home"] == 1][PC].mean(), rb[rb["home"] == 0][PC].mean()
    print("\n  RB ppg at HOME %.2f  |  AWAY %.2f  |  diff %.2f (%.1f%%)  n=%d"
          % (hm, aw, hm - aw, 100 * (hm - aw) / aw, len(rb)))

sch = grab("load_schedules", seasons=[2026])
rows = []
for _, r in sch.iterrows():
    rows.append((r["week"], fix(r["home_team"]), fix(r["away_team"]), 1))
    rows.append((r["week"], fix(r["away_team"]), fix(r["home_team"]), 0))
S = pd.DataFrame(rows, columns=["week", "team", "opp", "home"])
S["fpWR"] = S["opp"].map(p25)

agg = []
for tm, g in S.groupby("team"):
    po = g[g["week"].between(15, 17)]
    wk = set(g["week"])
    bye = [w for w in range(1, 19) if w not in wk]
    agg.append({"team": tm, "full": g["fpWR"].mean(),
                "playoff": po["fpWR"].mean() if len(po) else float("nan"),
                "away": int((g["home"] == 0).sum()),
                "bye": bye[0] if bye else 0})
T = pd.DataFrame(agg)
T["sos_rk"] = T["full"].rank(ascending=False).astype(int)
T["po_rk"] = T["playoff"].rank(ascending=False).astype(int)
LG = p25.mean()

b = pd.read_csv("board_ecr.csv")
b = b[b["position"] == "WR"].copy()
b["team"] = b["team"].map(fix)
m = b.merge(T, on="team", how="left").sort_values("sos_rk")

print("\n\n%s" % ("=" * 78))
print("WR SCHEDULE RANKINGS  (1 = easiest)   league avg fpWR allowed = %.1f" % LG)
print("=" * 78)
print("  full = avg fpWR his opponents allowed | vs = delta vs league avg")
print("  PO   = same for weeks 15-17 (fantasy playoffs)\n")
print("  rk  player                  tm   ECR   full     vs    PO  POrk  away  bye")
print("  " + "-" * 72)
for i, (_, r) in enumerate(m.iterrows(), 1):
    print("  %-3d %-23s %-4s %3d  %5.1f  %+5.1f  %5.1f  %3d   %2d   %2d"
          % (i, r["player"], r["team"], r["ecr"], r["full"], r["full"] - LG,
             r["playoff"], r["po_rk"], r["away"], r["bye"]))

print("\n  EASIEST 5 full-season:  %s" % ", ".join(m.head(5)["player"]))
print("  HARDEST 5 full-season:  %s" % ", ".join(m.tail(5)["player"]))
po = m.sort_values("po_rk")
print("\n  EASIEST 5 playoff wks:  %s" % ", ".join(po.head(5)["player"]))
print("  HARDEST 5 playoff wks:  %s" % ", ".join(po.tail(5)["player"]))
print("\n  spread across all RBs: %.1f to %.1f pts/gm (%.1f pt gap)"
      % (m["full"].min(), m["full"].max(), m["full"].max() - m["full"].min()))
