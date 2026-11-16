import pandas as pd

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def sv(k):
    return float(V.get(k, 0.0))

SP = pd.read_csv("stat_projections_2026.csv")
B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")

SP = SP[SP["position"].isin(["WR", "RB", "TE"])].copy()
for c in ["receptions", "receiving_yards",
          "receiving_tds", "rushing_yards",
          "rushing_tds", "carries"]:
    SP[c] = pd.to_numeric(SP[c], errors="coerce").fillna(0)
SP["raw"] = (SP["receptions"] * sv("rec")
             + SP["receiving_yards"] * sv("rec_yd")
             + SP["receiving_tds"] * sv("rec_td")
             + SP["rushing_yards"] * sv("rush_yd")
             + SP["rushing_tds"] * sv("rush_td"))

M = SP[["player_id", "player_display_name", "position",
        "raw"]].merge(
    B[["player_id", "pp", "rank", "pos_rank",
       "exp_games"]], on="player_id", how="inner")
M = M[M["pp"].notna() & (M["pp"] > 0)]
M["gap"] = 100.0 * (M["pp"] / M["raw"].clip(lower=0.01) - 1)
print("matched %d players" % len(M))

print("\n=== THE TWO IN QUESTION ===")
print("  %-20s %8s %8s %9s"
      % ("player", "raw ppg", "board", "shift"))
for nm in ["Jaylen Waddle", "Xavier Worthy"]:
    h = M[M["player_display_name"] == nm]
    if len(h):
        r = h.iloc[0]
        print("  %-20s %8.2f %8.2f %+8.1f%%"
              % (nm, r["raw"], r["pp"], r["gap"]))

print("\n=== HOW OFTEN DOES CALIBRATION REVERSE ORDER? ===")
for pos in ["WR", "RB", "TE"]:
    d = M[M["position"] == pos].reset_index(drop=True)
    if len(d) < 20:
        continue
    d = d.nlargest(60, "raw").reset_index(drop=True)
    rev = 0
    tot = 0
    worst = None
    for i in range(len(d)):
        for j in range(i + 1, len(d)):
            a, b = d.iloc[i], d.iloc[j]
            tot += 1
            if a["raw"] > b["raw"] and a["pp"] < b["pp"]:
                rev += 1
                sw = (b["pp"] - a["pp"]) + (a["raw"] - b["raw"])
                if worst is None or sw > worst[0]:
                    worst = (sw, a["player_display_name"],
                             b["player_display_name"],
                             a["raw"], a["pp"],
                             b["raw"], b["pp"])
    print("  %-4s %5d of %6d pairs reversed (%.1f%%)"
          % (pos, rev, tot, 100.0 * rev / max(tot, 1)))
    if worst:
        print("     worst: %s raw %.2f -> %.2f"
              % (worst[1][:20], worst[3], worst[4]))
        print("            %s raw %.2f -> %.2f"
              % (worst[2][:20], worst[5], worst[6]))

print("\n=== BIGGEST BOOSTS (calibration inflating) ===")
print("  %-22s %-4s %7s %7s %8s"
      % ("player", "pos", "raw", "board", "shift"))
for _, r in M.nlargest(10, "gap").iterrows():
    print("  %-22s %-4s %7.2f %7.2f %+7.1f%%"
          % (str(r["player_display_name"])[:22],
             r["position"], r["raw"], r["pp"], r["gap"]))
print("\n=== BIGGEST CUTS ===")
for _, r in M.nsmallest(10, "gap").iterrows():
    print("  %-22s %-4s %7.2f %7.2f %+7.1f%%"
          % (str(r["player_display_name"])[:22],
             r["position"], r["raw"], r["pp"], r["gap"]))
