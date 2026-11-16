import json
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
WHO = "Jaxon Smith-Njigba"

B = pd.read_csv("board_final.csv", low_memory=False)
h = B[B["player_display_name"].astype(str)
      .str.contains("Smith-Njigba", na=False)]
assert len(h), "JSN not on board"
r = h.sort_values("rank").iloc[0]
PID = str(r["player_id"])
TM = FIX.get(str(r["team"]).upper(), str(r["team"]).upper())
PPG = float(r["points"])
print("=== BOARD ROW ===")
print("  %s | %s | id %s" % (r["player_display_name"], TM, PID))
print("  rank %s overall, %s%s | %.2f ppg | %.0f over 17"
      % (r["rank"], r["position"], r["pos_rank"], PPG, PPG * 17))
print("  bye week %s | adp %s" % (r["bye"], r["adp"]))

S = pl(nfl.load_schedules(seasons=[2026]))
S["home_team"] = S["home_team"].astype(str).replace(FIX)
S["away_team"] = S["away_team"].astype(str).replace(FIX)
G = S[(S["home_team"] == TM) | (S["away_team"] == TM)].copy()
G["opp"] = np.where(G["home_team"] == TM,
                    G["away_team"], G["home_team"])
G["at"] = np.where(G["home_team"] == TM, "vs", "@")
G["d"] = pd.to_datetime(G["gameday"], errors="coerce")
G = G.sort_values("week").reset_index(drop=True)
G["rest"] = G["d"].diff().dt.days
played = set(G["week"].astype(int))
BYE = [w for w in range(1, 19) if w not in played]
print("\n=== 2026 SCHEDULE, %s ===" % TM)
print("  games %d | bye week %s"
      % (len(G), BYE[0] if BYE else "none"))
print("  %4s %-4s %-4s %-10s %-4s %5s"
      % ("wk", "", "opp", "date", "day", "rest"))
for _, x in G.iterrows():
    print("  %4d %-4s %-4s %-10s %-4s %5s"
          % (x["week"], x["at"], x["opp"],
             str(x["gameday"])[:10], str(x["weekday"])[:3],
             "--" if x["rest"] != x["rest"] else "%.0f" % x["rest"]))
G.to_csv("jsn_schedule.csv", index=False)

D = pd.read_csv("def_components.csv")
D["opponent_team"] = D["opponent_team"].astype(str).replace(FIX)
W25 = D[(D["season"] == 2025) & (D["position"] == "WR")].copy()
W25["ypt_rk"] = W25["ypt"].rank(ascending=True).astype(int)
W25["tpg_rk"] = W25["tpg"].rank(ascending=True).astype(int)
LG_YPT = float(W25["ypt"].mean())
LG_TPG = float(W25["tpg"].mean())
M = {r["opponent_team"]: r for _, r in W25.iterrows()}

print("\n=== WHAT EACH OPPONENT DID TO WRs IN 2025 ===")
print("  ypt = yards allowed per target | rank 1 = toughest")
print("  league mean %.2f ypt, %.1f WR targets/game"
      % (LG_YPT, LG_TPG))
print("\n  %4s %-3s %-4s %7s %6s %8s %6s %8s"
      % ("wk", "", "opp", "ypt", "rk", "tar/g", "rk", "dev"))
rows = []
for _, x in G.iterrows():
    o = M.get(x["opp"])
    if o is None:
        print("  %4d %-3s %-4s   no 2025 profile"
              % (x["week"], x["at"], x["opp"]))
        rows.append({"week": int(x["week"]), "dev": 1.0})
        continue
    dev = (o["ypt"] / LG_YPT)
    rows.append({"week": int(x["week"]), "dev": float(dev)})
    print("  %4d %-3s %-4s %7.2f %6d %8.1f %6d %+7.1f%%"
          % (x["week"], x["at"], x["opp"], o["ypt"],
             o["ypt_rk"], o["tpg"], o["tpg_rk"],
             100.0 * (dev - 1)))

R = pd.DataFrame(rows)
print("\n=== IF WE APPLIED THE MATCHUP AT FULL STRENGTH ===")
print("  ppg x opponent deviation, no shrink\n")
print("  %4s %-4s %8s %8s %8s"
      % ("wk", "opp", "flat", "k=0.10", "k=1.0"))
for _, x in G.iterrows():
    d = float(R[R["week"] == int(x["week"])]["dev"].iloc[0])
    print("  %4d %-4s %8.2f %8.2f %8.2f"
          % (x["week"], x["opp"], PPG,
             PPG * (1 + 0.10 * (d - 1)), PPG * d))
lo, hi = R["dev"].min(), R["dev"].max()
print("\n  softest matchup %+.1f%% | toughest %+.1f%%"
      % (100 * (hi - 1), 100 * (lo - 1)))
print("  full-strength weekly range: %.2f to %.2f ppg"
      % (PPG * lo, PPG * hi))
print("  at the tested k=0.10:      %.2f to %.2f ppg"
      % (PPG * (1 + 0.10 * (lo - 1)),
         PPG * (1 + 0.10 * (hi - 1))))
print("\n  k=0.10 is what survived train/valid/test in 181.")
print("  k=1.0 is what the raw 2025 numbers would suggest")
print("  if last year's defense repeated exactly.")
