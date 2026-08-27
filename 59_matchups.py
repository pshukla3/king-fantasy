import pandas as pd

TEAM = "DET"
PLAYER = "Jahmyr Gibbs"

def grab(fn, **kw):
    try:
        import nflreadpy as nfl
        r = getattr(nfl, fn)(**kw)
        return r.to_pandas() if hasattr(r, "to_pandas") else pd.DataFrame(r)
    except Exception as e:
        print("  %s failed: %s" % (fn, e))
        return None

sch = grab("load_schedules", seasons=[2026])
if sch is None:
    sch = pd.read_csv("schedules_2026.csv", low_memory=False)
print("schedule rows: %d" % len(sch))

g = sch[(sch["home_team"] == TEAM) | (sch["away_team"] == TEAM)].copy()
g["opp"] = [r["away_team"] if r["home_team"] == TEAM else r["home_team"]
            for _, r in g.iterrows()]
g["site"] = ["vs" if r["home_team"] == TEAM else "@" for _, r in g.iterrows()]
g = g.sort_values("week")[["week", "opp", "site"]].reset_index(drop=True)

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
oc = next((c for c in ["opponent_team", "opponent", "opp_team"] if c in H.columns), None)
pc = next((c for c in ["fantasy_points_ppr", "ppr_points"] if c in H.columns), None)
print("opponent col: %s | points col: %s" % (oc, pc))

d = H[(H["season"] == 2025) & H[oc].notna()].copy()
gm = d.groupby(oc)["week"].nunique().rename("gms")

def per_game(df, col, name):
    return (df.groupby(oc)[col].sum() / gm).rename(name)

parts = [gm]
for pos, lbl in [("RB", "fpRB"), ("WR", "fpWR"), ("TE", "fpTE"), ("QB", "fpQB")]:
    parts.append(per_game(d[d["position"] == pos], pc, lbl))
for col, lbl in [("rushing_yards", "ruYd"), ("carries", "ruAtt"),
                 ("receiving_yards", "reYd"), ("targets", "tgts")]:
    if col in d.columns:
        parts.append(per_game(d, col, lbl))

DEF = pd.concat(parts, axis=1).reset_index().rename(columns={oc: "opp"})
if "ruYd" in DEF and "ruAtt" in DEF:
    DEF["ypc"] = DEF["ruYd"] / DEF["ruAtt"].replace(0, float("nan"))
DEF["plays"] = DEF.get("ruAtt", 0) + DEF.get("tgts", 0)
DEF.to_csv("defense_2025.csv", index=False)
print("defense profiles built: %d teams" % len(DEF))

for c in ["fpRB", "ruYd", "ypc", "ruAtt", "fpWR", "reYd", "plays"]:
    if c in DEF.columns:
        DEF[c + "_rk"] = DEF[c].rank(ascending=False).astype(int)

m = g.merge(DEF, on="opp", how="left")

print("\n%s" % ("=" * 78))
print("%s (%s) — 2026 SCHEDULE vs 2025 DEFENSIVE PROFILES" % (PLAYER, TEAM))
print("=" * 78)
print("  fpRB = PPR points allowed to RBs per game (rank 1 = most generous)")
print("  ypc  = yards per carry allowed | ruAtt = carries faced per game")
print("  plays = carries + targets faced per game (time on defense proxy)\n")
print("  wk      opp    fpRB  rk    ypc  rk   ruAtt  rk   plays  rk")
print("  " + "-" * 60)
for _, r in m.iterrows():
    print("  %-3d  %-2s %-4s  %5.1f %3s  %5.2f %3s  %5.1f %3s  %5.1f %3s"
          % (r["week"], r["site"], r["opp"],
             r.get("fpRB", float("nan")), r.get("fpRB_rk", "-"),
             r.get("ypc", float("nan")), r.get("ypc_rk", "-"),
             r.get("ruAtt", float("nan")), r.get("ruAtt_rk", "-"),
             r.get("plays", float("nan")), r.get("plays_rk", "-")))

print("\n  season avg fpRB allowed by his opponents: %.1f  (league avg %.1f)"
      % (m["fpRB"].mean(), DEF["fpRB"].mean()))
print("  weeks vs bottom-10 rush defenses: %d"
      % int((m["fpRB_rk"] <= 10).sum()))
print("  weeks vs top-10 rush defenses:    %d"
      % int((m["fpRB_rk"] >= 23).sum()))
