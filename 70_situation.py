import pandas as pd

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = next(c for c in ["team", "recent_team"] if c in H.columns)
PC = "fantasy_points_ppr"
H = H[H["position"].isin(["RB", "WR", "TE"])].copy()
for c in ["carries", "targets"]:
    if c not in H.columns:
        H[c] = 0.0
H["opp"] = H["carries"].fillna(0) + H["targets"].fillna(0)

T = H.groupby([TC, "season"]).agg(
    opp=("opp", "sum"), tgt=("targets", "sum"), car=("carries", "sum"),
    pts=(PC, "sum"), wks=("week", "nunique")).reset_index()
T["opp_pg"] = T["opp"] / T["wks"]
T["pass_rate"] = T["tgt"] / T["opp"].replace(0, float("nan"))

nt = T[[TC, "season", "opp_pg", "pass_rate"]].copy()
nt["season"] = nt["season"] - 1
nt = nt.rename(columns={"opp_pg": "opp_pg_n", "pass_rate": "pass_rate_n"})
TT = T.merge(nt, on=[TC, "season"], how="inner")

print("=== TEAM CONTEXT: HOW REPEATABLE IS SCHEME? (year N vs N+1) ===")
print("  n = %d team-seasons" % len(TT))
print("  pass rate       r = %.3f   (range %.3f to %.3f)"
      % (TT["pass_rate"].corr(TT["pass_rate_n"]),
         T["pass_rate"].min(), T["pass_rate"].max()))
print("  plays per game  r = %.3f   (range %.1f to %.1f)"
      % (TT["opp_pg"].corr(TT["opp_pg_n"]), T["opp_pg"].min(), T["opp_pg"].max()))
print("\n  compare: RB defense persistence was 0.202, WR defense -0.085")

P = H.groupby(["player_id", "position", TC, "season"]).agg(
    opp=("opp", "sum"), pts=(PC, "sum"), g=("week", "nunique")).reset_index()
P = P.merge(T[[TC, "season", "opp"]].rename(columns={"opp": "team_opp"}),
            on=[TC, "season"])
P["share"] = P["opp"] / P["team_opp"].replace(0, float("nan"))
P["ppg"] = P["pts"] / P["g"]

nxt = P[["player_id", TC, "season", "share", "opp", "g", "ppg"]].copy()
nxt["season"] = nxt["season"] - 1
nxt = nxt.rename(columns={"share": "share_n", "opp": "opp_n",
                          "g": "g_n", "ppg": "ppg_n"})
J = P.merge(nxt, on=["player_id", TC, "season"], how="left")

gone = J[J["share_n"].isna()].groupby([TC, "season"])["share"].sum().reset_index()
gone = gone.rename(columns={"share": "vacated"})
gone["season"] = gone["season"] + 1

K = P.merge(gone, on=[TC, "season"], how="left")
K["vacated"] = K["vacated"].fillna(0.0)
prv = P[["player_id", TC, "season", "share", "g"]].copy()
prv["season"] = prv["season"] + 1
prv = prv.rename(columns={"share": "share_prev", "g": "g_prev"})
K = K.merge(prv, on=["player_id", TC, "season"], how="inner")
K = K[(K["g"] >= 8) & (K["g_prev"] >= 4)].copy()
K["d_share"] = K["share"] - K["share_prev"]

print("\n\n=== VACATED OPPORTUNITY: DOES IT PREDICT WHO GROWS? ===")
print("  vacated = share of team opportunity held by players who LEFT")
print("  d_share = returning player's change in team opportunity share")
print("  " + "-" * 56)
print("  pos      n    corr(vacated, d_share)   avg vacated")
for pos, x in K.groupby("position"):
    if len(x) < 60:
        continue
    print("  %-4s %6d          %+.3f              %.3f"
          % (pos, len(x), x["vacated"].corr(x["d_share"]), x["vacated"].mean()))
print("  ALL  %6d          %+.3f              %.3f"
      % (len(K), K["vacated"].corr(K["d_share"]), K["vacated"].mean()))

print("\n  --- how much share does a returner absorb per point vacated? ---")
for pos, x in K.groupby("position"):
    if len(x) < 60:
        continue
    v = x["vacated"]
    slope = ((v - v.mean()) * (x["d_share"] - x["d_share"].mean())).sum() / \
            ((v - v.mean()) ** 2).sum()
    print("  %-4s  slope = %+.3f  (of every vacated point, a given returner takes %.0f%%)"
          % (pos, slope, 100 * slope))

rost = pd.read_csv("rosters_2026.csv", low_memory=False)
act = set(rost["gsis_id"].dropna())
L = P[P["season"] == 2025].copy()
cur = rost[["gsis_id", "team"]].dropna(subset=["gsis_id"]).drop_duplicates(
    "gsis_id").rename(columns={"gsis_id": "player_id", "team": "tm26"})
L = L.merge(cur, on="player_id", how="left")
L["stays"] = (L["tm26"] == L[TC]) & L["player_id"].isin(act)
V = L.groupby(TC).apply(
    lambda x: pd.Series({
        "vacated": x.loc[~x["stays"], "share"].sum(),
        "vac_car": x.loc[~x["stays"], "opp"].sum(),
        "who": ", ".join(x.loc[~x["stays"]].nlargest(2, "share")["player_id"])}),
    include_groups=False).reset_index()

print("\n\n=== 2026: WHERE THE OPPORTUNITY WENT MISSING ===")
print("  share of 2025 team opportunity now held by nobody on the roster")
print(V.nlargest(12, "vacated")[[TC, "vacated", "vac_car"]].round(3).to_string(index=False))
print("\n  your guys' teams:")
for t in ["JAX", "LAC", "CHI", "SEA", "DAL", "CIN", "IND", "NE", "PIT", "SF", "ATL"]:
    h = V[V[TC] == t]
    if len(h):
        print("    %-4s vacated %.1f%% of team opportunity" % (t, 100 * h["vacated"].iloc[0]))
V.to_csv("vacated_2026.csv", index=False)
print("\nSaved vacated_2026.csv")
