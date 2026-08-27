import pandas as pd, numpy as np

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = "team" if "team" in H.columns else "recent_team"
PC = "fantasy_points_ppr"
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
R = ["QB1", "RB1", "RB2", "WR1", "WR2", "WR3", "TE1"]
S = S[S["role"].isin(R)]
H = H.merge(S[["player_id", TC, "season", "role"]], on=["player_id", TC, "season"])
print("role-tagged player-weeks: %d" % len(H))

W = H.pivot_table(index=[TC, "season", "week"], columns="role",
                  values=PC, aggfunc="sum").reset_index()
have = [r for r in R if r in W.columns]
for c in have:
    g = W.groupby([TC, "season"])[c]
    W[c] = (W[c] - g.transform("mean")) / g.transform("std").replace(0, np.nan)
print("team-weeks: %d" % len(W))

C = W[have].corr(min_periods=300)
print("\n=== TEAMMATE CORRELATION (within-season weekly z-scores) ===")
print("  positive = boom together | 0 = independent\n")
print(C.round(3).to_string())

rows = []
for i, a in enumerate(have):
    for b in have[i + 1:]:
        rows.append({"pair": "%s/%s" % (a, b), "r": C.loc[a, b],
                     "n": int(W[[a, b]].dropna().shape[0])})
P = pd.DataFrame(rows).sort_values("r", ascending=False)
print("\n--- pairs sorted by strength ---")
print(P.round(3).to_string(index=False))
P.to_csv("teammate_corr.csv", index=False)

yrs = sorted(W["season"].unique())
mid = yrs[len(yrs) // 2]
E = W[W["season"] < mid][have].corr(min_periods=100)
L = W[W["season"] >= mid][have].corr(min_periods=100)
cm = []
for i, a in enumerate(have):
    for b in have[i + 1:]:
        cm.append({"pair": "%s/%s" % (a, b), "early": E.loc[a, b], "late": L.loc[a, b]})
M = pd.DataFrame(cm)
print("\n=== IS IT STABLE? split at season %d ===" % mid)
print(M.round(3).to_string(index=False))
print("\n  early vs late: r = %.3f | mean absolute drift = %.3f"
      % (M["early"].corr(M["late"]), (M["late"] - M["early"]).abs().mean()))
print("\nSaved teammate_corr.csv")
