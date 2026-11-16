import json, re, sys
import nflreadpy as nfl
import pandas as pd

NAME = " ".join(sys.argv[1:]) or "Jaxon Smith-Njigba"

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

K = norm(NAME)
print("=" * 60)
print("AGENT DOSSIER: %s" % NAME)
print("=" * 60)

# ---- identity -------------------------------------
B = json.load(open("site/_board.json"))["rows"]
row = next((r for r in B if norm(r["n"]) == K), None)
if not row:
    print("not on board"); sys.exit(1)
GS = row["pid"]
print("\n[IDENTITY]")
print("  %s  %s %s  gsis=%s"
      % (row["n"], row["pos"], row["tm"], GS))
print("  rank #%s (%s%s)  tier %s  bye %s  status %s"
      % (row.get("rk"), row.get("pos"), row.get("posrk"),
         row.get("tier"), row.get("bye"),
         row.get("inj") or "Active"))
print("  projection  live %.1f  floor %.1f  ceil %.1f"
      % (row.get("live") or 0, row.get("floor") or 0,
         row.get("ceil") or 0))

# ---- game log --------------------------------------
print("\n[GAME LOG]")
H = json.load(open("site/_hist.json")).get(GS, [])
for g in H[-10:]:
    print("    %s wk%-2d  %6.1f pts" % (g["t"], g["w"], g["p"]))
if H:
    pts = [g["p"] for g in H]
    import statistics as st
    print("  last %d: mean %.1f  median %.1f  sd %.1f"
          % (len(pts), st.mean(pts), st.median(pts),
             st.pstdev(pts) if len(pts) > 1 else 0))
    boom = sum(1 for p in pts if p >= 20)
    bust = sum(1 for p in pts if p < 8)
    print("  20+ games: %d (%.0f%%)   under 8: %d (%.0f%%)"
          % (boom, 100.0 * boom / len(pts),
             bust, 100.0 * bust / len(pts)))

# ---- snaps + opponent ------------------------------
print("\n[SNAPS BY GAME]")
try:
    sn = nfl.load_snap_counts(seasons=[2025, 2026]).to_pandas()
    m = sn[sn["player"].apply(norm) == K]
    m = m.sort_values(["season", "week"]).tail(10)
    for _, r in m.iterrows():
        print("    %d wk%-2d vs %-4s  %3.0f snaps  %.0f%%"
              % (r["season"], r["week"], r["opponent"],
                 r["offense_snaps"] or 0,
                 100 * (r["offense_pct"] or 0)))
    if len(m):
        print("  recent snap share: %.0f%%"
              % (100 * m["offense_pct"].tail(4).mean()))
except Exception as e:
    print("  snaps unavailable: %s" % str(e)[:70])

# ---- next gen stats --------------------------------
print("\n[NEXT GEN STATS]")
pos = row["pos"]
kind = ("receiving" if pos in ("WR", "TE") else
        ("rushing" if pos == "RB" else "passing"))
try:
    ng = nfl.load_nextgen_stats(seasons=[2025, 2026],
                                stat_type=kind).to_pandas()
    m = ng[ng["player_display_name"].apply(norm) == K]
    m = m[m["week"] > 0].sort_values(["season", "week"])
    if kind == "receiving":
        cols = ["avg_separation", "avg_cushion",
                "avg_intended_air_yards",
                "percent_share_of_intended_air_yards",
                "catch_percentage",
                "avg_yac_above_expectation"]
    elif kind == "rushing":
        cols = ["efficiency", "avg_time_to_los",
                "rush_yards_over_expected_per_att",
                "percent_attempts_gte_eight_defenders"]
    else:
        cols = ["avg_time_to_throw", "avg_air_yards_differential",
                "aggressiveness", "completion_percentage_above_expectation"]
    cols = [c for c in cols if c in m.columns]
    if len(m) and cols:
        print("  %-8s %s" % ("WK", "  ".join(
            "%-10s" % c[:10] for c in cols)))
        for _, r in m.tail(6).iterrows():
            print("  %d-%-4d %s"
                  % (r["season"], r["week"], "  ".join(
                      "%-10.2f" % (r[c] if pd.notna(r[c]) else 0)
                      for c in cols)))
        print("\n  league rank this season:")
        cur = ng[(ng["season"] == 2026) & (ng["week"] == 0)]
        if not len(cur):
            cur = ng[ng["season"] == 2026]
        for c in cols:
            same = cur[cur["player_position"] == pos]
            if not len(same) or c not in same.columns:
                continue
            v = m[c].tail(4).mean()
            pct = (same[c] < v).mean() * 100
            print("    %-36s %6.2f  (%.0fth pctile)"
                  % (c, v, pct))
    else:
        print("  no NGS rows for this player/type")
except Exception as e:
    print("  NGS unavailable: %s" % str(e)[:70])

# ---- target share ----------------------------------
print("\n[TARGET SHARE]")
try:
    ps = nfl.load_player_stats(seasons=[2026]).to_pandas()
    tm = row["tm"]
    col = "team" if "team" in ps.columns else "recent_team"
    t = ps[ps[col] == tm]
    for wk in sorted(t["week"].unique()):
        w = t[t["week"] == wk]
        tot = w["targets"].sum()
        mine = w[w["player_display_name"].apply(norm) == K]
        mt = mine["targets"].sum() if len(mine) else 0
        if tot:
            print("    wk%-2d  %2.0f of %2.0f team targets"
                  "  = %.0f%%" % (wk, mt, tot, 100 * mt / tot))
except Exception as e:
    print("  unavailable: %s" % str(e)[:70])

# ---- schedule ahead --------------------------------
print("\n[SCHEDULE AHEAD]")
try:
    S = json.load(open("site/_sched.json"))["sched"]
    mine = S.get(row["tm"], {})
    for w in sorted(mine, key=lambda x: int(x))[:8]:
        if int(w) < 2:
            continue
        g = mine[w]
        print("    wk%-3s %s %-4s  %s"
              % (w, g.get("at"), g.get("o"), g.get("t")))
except Exception as e:
    print("  unavailable: %s" % str(e)[:70])

# ---- news + injury ---------------------------------
print("\n[NEWS]")
PN = json.load(open("site/_pnews.json")).get(K)
if PN:
    for it in (PN.get("items") or [])[:4]:
        print("    %s  (%s)" % (it["t"][:70], it.get("s")))
    if PN.get("line"):
        print("    note: %s" % PN["line"][:120])
else:
    print("    no matched news")

RS = json.load(open("site/_reasons.json")).get(K)
if RS:
    print("\n[MODEL REASONING]")
    print("    %s" % RS.get("line"))
