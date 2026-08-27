import pandas as pd, numpy as np

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = "team" if "team" in H.columns else "recent_team"
OC = "opponent_team"
PC = "fantasy_points_ppr"
if OC not in H.columns:
    raise SystemExit("no opponent_team column - cannot measure this")

AC = next((c for c in ["attempts", "pass_attempts"] if c in H.columns), None)
for c in ["carries", "targets"]:
    if c not in H.columns:
        H[c] = 0.0
H["o"] = (H["carries"].fillna(0) + H["targets"].fillna(0)
          + (H[AC].fillna(0) if AC else 0.0))
H = H[H["position"].isin(["QB", "RB", "WR", "TE"])].copy()

S = H.groupby(["player_id", "position", TC, "season"])["o"].sum().reset_index()
S["rk"] = S.groupby([TC, "season", "position"])["o"].rank(ascending=False, method="first")
S["role"] = S["position"] + S["rk"].astype(int).astype(str)
R = ["QB1", "RB1", "WR1", "TE1"]
S = S[S["role"].isin(R)]
H = H.merge(S[["player_id", TC, "season", "role"]], on=["player_id", TC, "season"])

W = H.pivot_table(index=[TC, "season", "week"], columns="role",
                  values=PC, aggfunc="sum").reset_index()
have = [r for r in R if r in W.columns]
for c in have:
    g = W.groupby([TC, "season"])[c]
    W[c] = (W[c] - g.transform("mean")) / g.transform("std").replace(0, np.nan)

G = H[["season", "week", TC, OC]].dropna().drop_duplicates()
W = W.merge(G, on=[TC, "season", "week"], how="left")

A = W.rename(columns={c: "a_" + c for c in have}).rename(columns={TC: "tm", OC: "opp"})
B = W.rename(columns={c: "b_" + c for c in have}).rename(columns={TC: "opp2"})
B = B[["opp2", "season", "week"] + ["b_" + c for c in have]]
M = A.merge(B, left_on=["opp", "season", "week"],
            right_on=["opp2", "season", "week"], how="inner")
print("paired team-weeks (same NFL game): %d" % len(M))

print("\n=== OPPOSING-PLAYER CORRELATION ===")
print("  positive = shootout, both sides score | 0 = independent\n")
rows = []
for a in have:
    for b in have:
        x = M[["a_" + a, "b_" + b]].dropna()
        if len(x) < 300:
            continue
        rows.append({"mine": a, "theirs": b,
                     "r": x["a_" + a].corr(x["b_" + b]), "n": len(x)})
O = pd.DataFrame(rows).sort_values("r", ascending=False)
print(O.round(3).to_string(index=False))
O.to_csv("opponent_corr.csv", index=False)
print("\n  mean absolute r across all pairs: %.3f" % O["r"].abs().mean())
print("\n  if that mean is under ~0.05, cross-game correlation is not worth modeling")
print("Saved opponent_corr.csv")
