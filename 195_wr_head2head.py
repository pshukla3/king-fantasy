import json
import pandas as pd
import nflreadpy as nfl

def pl(d):
    return d.to_pandas() if hasattr(d, "to_pandas") else d

NAMES = ["Jaylen Waddle", "Xavier Worthy"]
B = pd.read_csv("board_final.csv", low_memory=False)
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def sv(k):
    return float(V.get(k, 0.0))

print("=== WHERE THE BOARD HAS THEM ===")
for nm in NAMES:
    h = B[B["player_display_name"] == nm]
    if not len(h):
        print("  %-20s NOT ON BOARD" % nm)
        continue
    r = h.iloc[0]
    print("  %-20s %s  %s%d  rank %d  %.2f ppg  ADP %s"
          % (nm, r["team"], r["position"],
             r["pos_rank"], r["rank"], r["points"],
             "--" if r["adp"] != r["adp"]
             else "%.1f" % r["adp"]))

W = pl(nfl.load_player_stats(seasons=list(range(2021, 2026))))
for c in ["targets", "receptions", "receiving_yards",
          "receiving_tds"]:
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0)
W = W[W["player_display_name"].isin(NAMES)]
S = W.groupby(["player_display_name", "season"]).agg(
    g=("week", "nunique"), tar=("targets", "sum"),
    rec=("receptions", "sum"),
    yds=("receiving_yards", "sum"),
    td=("receiving_tds", "sum")).reset_index()
S["ppg"] = (S["rec"] * sv("rec")
            + S["yds"] * sv("rec_yd")
            + S["td"] * sv("rec_td")) / S["g"]

print("\n=== CAREER, ACTUAL ===")
print("  %-18s %4s %3s %5s %5s %6s %4s %7s %7s %6s"
      % ("player", "yr", "g", "tar", "rec", "yds",
         "td", "tar/g", "yds/rec", "ppg"))
for nm in NAMES:
    d = S[S["player_display_name"] == nm]
    for _, x in d.sort_values("season").iterrows():
        print("  %-18s %4d %3d %5.0f %5.0f %6.0f %4.0f"
              " %7.1f %7.1f %6.2f"
              % (nm[:18], x["season"], x["g"], x["tar"],
                 x["rec"], x["yds"], x["td"],
                 x["tar"] / x["g"],
                 x["yds"] / max(x["rec"], 1), x["ppg"]))
    print()

print("=== RECENCY-WEIGHTED RATES (decay 0.4) ===")
print("  %-18s %8s %8s %9s %9s"
      % ("player", "tar/g", "catch%", "yds/rec", "td/rec"))
for nm in NAMES:
    d = S[S["player_display_name"] == nm]
    if not len(d):
        continue
    w = 0.4 ** (2025 - d["season"])
    tg = (w * d["tar"]).sum() / (w * d["g"]).sum()
    cr = (w * d["rec"]).sum() / (w * d["tar"]).sum()
    yr = (w * d["yds"]).sum() / (w * d["rec"]).sum()
    tr = (w * d["td"]).sum() / (w * d["rec"]).sum()
    print("  %-18s %8.2f %7.1f%% %9.2f %9.4f"
          % (nm[:18], tg, 100 * cr, yr, tr))

C = json.load(open("player_cards.json"))
print("\n=== OUR 2026 PROJECTION COMPONENTS ===")
print("  %-18s %5s %5s %6s %5s"
      % ("player", "tar", "rec", "yds", "td"))
for nm in NAMES:
    hit = [v for v in C.values() if v["nm"] == nm]
    if hit and "p26" in hit[0]:
        p = hit[0]["p26"]
        print("  %-18s %5.0f %5.0f %6.0f %5.1f"
              % (nm[:18], p["tar"], p["rec"],
                 p["cyd"], p["ctd"]))

print("\n=== TARGET COMPETITION ON THEIR NEW TEAMS ===")
for nm, tm in [("Jaylen Waddle", "DEN"),
               ("Xavier Worthy", "KC")]:
    d = B[(B["team"] == tm)
          & (B["position"].isin(["WR", "TE", "RB"]))]
    d = d[pd.to_numeric(d["points"],
                        errors="coerce").fillna(0) > 0]
    d = d.sort_values("points", ascending=False)
    print("\n  %s pass-catchers (%s):" % (tm, nm))
    for _, x in d.head(5).iterrows():
        me = "  <-- him" if x["player_display_name"] == nm else ""
        print("    %-24s %-4s %6.2f ppg%s"
              % (str(x["player_display_name"])[:24],
                 x["position"], float(x["points"]), me))
