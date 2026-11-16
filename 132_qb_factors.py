import pandas as pd

H = pd.read_csv("weekly_stats_long_history.csv",
                low_memory=False)
PC = "fantasy_points_ppr"
TC = "team" if "team" in H.columns else "recent_team"
OC = "opponent_team"
print("rows %d | team col %s | opp col %s"
      % (len(H), TC, OC in H.columns))

Q = H[H["position"] == "QB"].copy()

D = Q.groupby([OC, "season"]).agg(
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
D["fpQB"] = D["pts"] / D["g"]
N = D.copy()
N["season"] = N["season"] - 1
N = N.rename(columns={"fpQB": "next"})[[OC, "season", "next"]]
M = D.merge(N, on=[OC, "season"], how="inner")

print("\n=== 1. DOES QB DEFENSE PERSIST? ===")
print("  n = %d team-season pairs" % len(M))
print("  fantasy pts allowed to QBs, yr N vs N+1")
print("  r = %+.3f" % M["fpQB"].corr(M["next"]))
print("  compare: vs RB +0.202 | vs WR -0.085")
print("  spread %.1f to %.1f ppg allowed"
      % (D["fpQB"].min(), D["fpQB"].max()))

def col(df, c):
    if c in df.columns:
        return pd.to_numeric(df[c], errors="coerce").fillna(0)
    return None

SK = None
for c in ["sacks", "sacks_suffered", "times_sacked"]:
    v = col(Q, c)
    if v is not None and v.sum() > 0:
        SK = c
        break
print("\n=== 2. OFFENSIVE LINE (sack rate allowed) ===")
print("  sack column: %s" % SK)
if SK is None:
    print("  not in the weekly file - needs pbp")
else:
    Q["_sk"] = col(Q, SK)
    Q["_at"] = col(Q, "attempts")
    T = Q.groupby([TC, "season"]).agg(
        sk=("_sk", "sum"), at=("_at", "sum"),
        pts=(PC, "sum"), g=("week", "nunique")).reset_index()
    T = T[T["at"] > 100].copy()
    T["skrate"] = T["sk"] / (T["at"] + T["sk"])
    T["ppg"] = T["pts"] / T["g"]
    X = T.copy()
    X["season"] = X["season"] - 1
    X = X.rename(columns={"skrate": "nsk", "ppg": "nppg"})
    X = X[[TC, "season", "nsk", "nppg"]]
    P = T.merge(X, on=[TC, "season"], how="inner")
    print("  n = %d team-seasons" % len(P))
    print("  sack rate persistence      r = %+.3f"
          % P["skrate"].corr(P["nsk"]))
    print("  sack rate vs QB ppg same yr r = %+.3f"
          % T["skrate"].corr(T["ppg"]))
    print("  sack rate vs QB ppg NEXT yr r = %+.3f"
          % P["skrate"].corr(P["nppg"]))
    print("  range %.3f to %.3f"
          % (T["skrate"].min(), T["skrate"].max()))

RC = H[H["position"].isin(["WR", "TE"])].copy()
S = RC.groupby(["player_id", TC, "season"]).agg(
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
S["ppg"] = S["pts"] / S["g"]
S = S[S["g"] >= 6]
t3 = S.sort_values("ppg", ascending=False).groupby(
    [TC, "season"]).head(3)
CO = t3.groupby([TC, "season"])["ppg"].sum()
CO = CO.rename("corps").reset_index()

QS = Q.groupby(["player_id", TC, "season"]).agg(
    pts=(PC, "sum"), g=("week", "nunique")).reset_index()
QS = QS[QS["g"] >= 8].copy()
QS["ppg"] = QS["pts"] / QS["g"]
QS = QS.merge(CO, on=[TC, "season"], how="left")

NX = QS[["player_id", "season", "ppg"]].copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"ppg": "ppg_n"})
J = QS.merge(NX, on=["player_id", "season"], how="inner")
J = J.dropna(subset=["ppg", "ppg_n", "corps"])

print("\n=== 3. RECEIVING CORPS QUALITY ===")
print("  corps = sum of team's top 3 WR/TE ppg")
print("  n = %d QB season pairs" % len(J))
print("  corps vs QB ppg same year  r = %+.3f"
      % J["corps"].corr(J["ppg"]))
print("  corps vs QB ppg next year  r = %+.3f"
      % J["corps"].corr(J["ppg_n"]))

yrs = sorted(J["season"].unique())
cut = yrs[int(len(yrs) * 0.6)]
TR = J[J["season"] < cut].copy()
TS = J[J["season"] >= cut].copy()
b0 = TR["ppg"].cov(TR["ppg_n"]) / TR["ppg"].var()
a0 = TR["ppg_n"].mean() - b0 * TR["ppg"].mean()
TR["res"] = TR["ppg_n"] - (a0 + b0 * TR["ppg"])
b1 = TR["corps"].cov(TR["res"]) / TR["corps"].var()
a1 = TR["res"].mean() - b1 * TR["corps"].mean()
base = a0 + b0 * TS["ppg"]
add = base + (a1 + b1 * TS["corps"])
r0 = base.corr(TS["ppg_n"])
r1 = add.corr(TS["ppg_n"])
print("\n  train < %d (n=%d) | test >= %d (n=%d)"
      % (cut, len(TR), cut, len(TS)))
print("  baseline, own ppg only  r %.3f" % r0)
print("  + corps quality         r %.3f" % r1)
print("  gain %+.3f  | threshold +0.010" % (r1 - r0))
print("  DECISION: %s"
      % ("ADOPT" if r1 - r0 > 0.010 else "REJECT"))
