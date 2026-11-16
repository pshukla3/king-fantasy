import pandas as pd
import nflreadpy as nfl

YRS = [2021, 2022, 2023, 2024, 2025]
print("pulling pbp for interceptions...")
P = nfl.load_pbp(seasons=YRS)
P = P.to_pandas() if hasattr(P, "to_pandas") else P
P = P[P["passer_player_id"].notna()].copy()
for c in ["interception", "pass_attempt"]:
    P[c] = pd.to_numeric(P[c], errors="coerce").fillna(0)

G = P.groupby("passer_player_id").agg(
    att=("pass_attempt", "sum"),
    ints=("interception", "sum")).reset_index()
G = G.rename(columns={"passer_player_id": "player_id"})
LG = G["ints"].sum() / G["att"].sum()
K = 900
G["rate"] = (G["ints"] + K * LG) / (G["att"] + K)
G = G[G["att"] >= 100].sort_values("att",
                                   ascending=False)
G.to_csv("qb_int_rates.csv", index=False)
print("league int rate %.4f | QBs %d" % (LG, len(G)))
print("\n  lowest 8")
print(G.nsmallest(8, "rate")[
    ["player_id", "att", "ints", "rate"]].round(4)
      .to_string(index=False))
print("\n  highest 8")
print(G.nlargest(8, "rate")[
    ["player_id", "att", "ints", "rate"]].round(4)
      .to_string(index=False))
