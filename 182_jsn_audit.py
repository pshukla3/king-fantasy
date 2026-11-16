import json
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

NAME = "Jaxon Smith-Njigba"
B = pd.read_csv("board_final.csv", low_memory=False)
row = B[B["player_display_name"].astype(str) == NAME]
assert len(row), "JSN not on board"
r = row.iloc[0]
PID = str(r["player_id"])
print("=== BOARD ROW ===")
print("  id %s | team %s | rank %s | WR%s"
      % (PID, r["team"], r["rank"], r["pos_rank"]))
print("  points %.2f ppg | vorp %.2f | adp %s"
      % (float(r["points"]), float(r["vorp"]), r["adp"]))

W = pl(nfl.load_player_stats(seasons=[2022, 2023, 2024, 2025]))
W["player_id"] = W["player_id"].astype(str)
W = W[W["player_id"] == PID]
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
NUM = ["targets", "receptions", "receiving_yards",
       "receiving_tds", "carries", "rushing_yards",
       "rushing_tds", "fantasy_points_ppr"]
for c in NUM:
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)
S = W.groupby("season").agg(
    g=("week", "nunique"),
    tar=("targets", "sum"), rec=("receptions", "sum"),
    yds=("receiving_yards", "sum"),
    td=("receiving_tds", "sum"),
    fp=("fantasy_points_ppr", "sum")).reset_index()
print("\n=== CAREER, ACTUAL ===")
print("  %4s %3s %5s %5s %6s %4s %7s %7s %7s %6s"
      % ("yr", "g", "tar", "rec", "yds", "td",
         "tar/g", "catch%", "yds/rec", "ppg"))
for _, x in S.iterrows():
    print("  %4d %3d %5.0f %5.0f %6.0f %4.0f %7.1f"
          " %7.1f%% %7.1f %6.2f"
          % (x["season"], x["g"], x["tar"], x["rec"],
             x["yds"], x["td"], x["tar"] / x["g"],
             100.0 * x["rec"] / max(x["tar"], 1),
             x["yds"] / max(x["rec"], 1),
             x["fp"] / x["g"]))

print("\n=== RECENCY-WEIGHTED RATES ===")
print("  decay 1.0 = all seasons equal")
print("  decay 0.4 = what the QB model uses\n")
print("  %6s %8s %9s %9s %9s"
      % ("decay", "tar/g", "catch%", "yds/rec", "td/rec"))
for d in [1.0, 0.6, 0.4, 0.3]:
    w = d ** (2025 - S["season"])
    tg = (w * S["tar"]).sum() / (w * S["g"]).sum()
    cr = (w * S["rec"]).sum() / (w * S["tar"]).sum()
    yr = (w * S["yds"]).sum() / (w * S["rec"]).sum()
    tr = (w * S["td"]).sum() / (w * S["rec"]).sum()
    print("  %6.1f %8.2f %8.1f%% %9.2f %9.4f"
          % (d, tg, 100 * cr, yr, tr))

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))
SP = pd.read_csv("stat_projections_2026.csv")
SP["player_id"] = SP["player_id"].astype(str)
p = SP[SP["player_id"] == PID]
print("\n=== 2026 PROJECTED COMPONENTS ===")
if not len(p):
    print("  NOT IN stat_projections_2026 - board value"
          " came from elsewhere")
else:
    q = p.iloc[0]
    tar = float(q["targets"])
    rec = float(q["receptions"])
    yds = float(q["receiving_yards"])
    td = float(q["receiving_tds"])
    car = float(q["carries"])
    ryd = float(q["rushing_yards"])
    rtd = float(q["rushing_tds"])
    print("  per game : %.1f tar  %.1f rec  %.1f yds"
          "  %.2f td" % (tar, rec, yds, td))
    print("  x17      : %.0f tar  %.0f rec  %.0f yds"
          "  %.1f td"
          % (tar * 17, rec * 17, yds * 17, td * 17))
    print("  catch%%   : %.1f%%   yds/rec %.2f"
          % (100.0 * rec / max(tar, 1), yds / max(rec, 1)))
    raw = (rec * float(V["rec"])
           + yds * float(V["rec_yd"])
           + td * float(V["rec_td"])
           + ryd * float(V["rush_yd"])
           + rtd * float(V["rush_td"]))
    print("\n=== POINTS FROM COMPONENTS (uncalibrated) ===")
    print("  receptions %.1f x 1.0   = %6.2f"
          % (rec, rec * float(V["rec"])))
    print("  rec yards  %.1f x 0.1   = %6.2f"
          % (yds, yds * float(V["rec_yd"])))
    print("  rec TDs    %.2f x 6.0   = %6.2f"
          % (td, td * float(V["rec_td"])))
    print("  rushing                 = %6.2f"
          % (ryd * float(V["rush_yd"])
             + rtd * float(V["rush_td"])))
    print("  " + "-" * 34)
    print("  RAW PROJECTION          = %6.2f ppg" % raw)
    bp = float(r["points"])
    print("  BOARD (after calib)     = %6.2f ppg" % bp)
    print("  calibration effect      = %+6.2f  (%+.1f%%)"
          % (bp - raw, 100.0 * (bp / raw - 1)))
    a25 = S[S["season"] == 2025]
    if len(a25):
        x = a25.iloc[0]
        act = x["fp"] / x["g"]
        print("\n=== VS HIS 2025 ===")
        print("  2025 actual  %.2f ppg" % act)
        print("  raw 2026     %.2f ppg  (%+.1f%%)"
              % (raw, 100.0 * (raw / act - 1)))
        print("  board 2026   %.2f ppg  (%+.1f%%)"
              % (bp, 100.0 * (bp / act - 1)))
    print("\n=== SEASON LINE, BOARD-SCALED ===")
    sc = bp / raw if raw else 1.0
    print("  catches   %.0f" % (rec * 17 * sc))
    print("  rec yards %.0f" % (yds * 17 * sc))
    print("  rec TDs   %.1f" % (td * 17 * sc))
    print("  targets   %.0f  (volume, not scaled)"
          % (tar * 17))
    print("  season pts %.0f" % (bp * 17))
