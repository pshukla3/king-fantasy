import pandas as pd, numpy as np

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
TC = next(c for c in ["team", "recent_team"] if c in H.columns)
AC = next((c for c in ["attempts", "pass_attempts"] if c in H.columns), None)
H = H[H["position"].isin(["QB", "RB", "WR", "TE"])].copy()
for c in ["carries", "targets", "receptions", "rushing_yards", "rushing_tds",
          "receiving_yards", "receiving_tds", "passing_yards", "passing_tds",
          "interceptions"]:
    if c not in H.columns:
        H[c] = 0.0
    H[c] = H[c].fillna(0.0)
H["att"] = H[AC].fillna(0.0) if AC else 0.0
H["pts"] = (H["rushing_yards"] * 0.1 + H["rushing_tds"] * 6 + H["receptions"]
            + H["receiving_yards"] * 0.1 + H["receiving_tds"] * 6
            + H["passing_yards"] * 0.04 + H["passing_tds"] * 4
            - H["interceptions"] * 2)
H["opp"] = H["carries"] + H["targets"] + H["att"]

S = H.groupby(["player_id", "position", TC, "season"]).agg(
    g=("week", "nunique"), pts=("pts", "sum"), opp=("opp", "sum")).reset_index()
S = S[S["g"] >= 3].copy()
S["ppg"] = S["pts"] / S["g"]
S["opg"] = S["opp"] / S["g"]
S["eff"] = S["pts"] / S["opp"].replace(0, np.nan)
S["role"] = S.groupby([TC, "season", "position"])["opp"].rank(
    ascending=False, method="first")

B = S[S["role"] <= 4].groupby(["position", "role"]).apply(
    lambda x: x["opp"].sum() / x["g"].sum(), include_groups=False).rename("opg_role").reset_index()

nx = S[["player_id", "season", "ppg", "role", "g"]].copy()
nx["season"] = nx["season"] - 1
nx = nx.rename(columns={"ppg": "ppg_n", "role": "role_n", "g": "g_n"})
D = S.merge(nx, on=["player_id", "season"], how="inner")
D = D[(D["g_n"] >= 8) & (D["opp"] >= 20)]
D = D.merge(B.rename(columns={"role": "role_n"}), on=["position", "role_n"], how="left")
D = D.dropna(subset=["opg_role", "eff"])
D["role_proj"] = D["eff"] * D["opg_role"]

W, REL = {}, {}
print("=== MEASURED BLEND: HOW MUCH ROLE vs HOW MUCH HISTORY ===")
print("  pos     n     raw    role   blended   w_role")
print("  " + "-" * 48)
for pos, x in D.groupby("position"):
    if len(x) < 60:
        continue
    ra, rr = x["ppg"].corr(x["ppg_n"]), x["role_proj"].corr(x["ppg_n"])
    bw, br = 0.0, -1.0
    for i in range(21):
        w = i / 20.0
        r = (w * x["role_proj"] + (1 - w) * x["ppg"]).corr(x["ppg_n"])
        if r > br:
            br, bw = r, w
    W[pos], REL[pos] = bw, ra
    print("  %-4s %5d   %.3f   %.3f    %.3f     %.2f" % (pos, len(x), ra, rr, br, bw))

BINS = [0, 60, 120, 220, 350, 99999]
LAB = ["<60", "60-120", "120-220", "220-350", "350+"]
D2 = S.merge(nx, on=["player_id", "season"], how="inner")
D2 = D2[D2["g_n"] >= 8].copy()
D2["bkt"] = pd.cut(D2["opp"], bins=BINS, labels=LAB)
CONF = {}
for b, x in D2.groupby("bkt", observed=True):
    if len(x) >= 40:
        CONF[str(b)] = x["ppg"].corr(x["ppg_n"])
hi = np.mean([v for k, v in CONF.items() if k in ("120-220", "220-350", "350+")])
CONF = {k: min(v / hi, 1.0) for k, v in CONF.items()}
print("\n  low-sample confidence (capped at 1.0 above 120 opportunities):")
print("   ", {k: round(v, 3) for k, v in CONF.items()})

X = pd.read_csv("top100_situational.csv", low_memory=False)
for c in ["car", "tgt", "att"]:
    if c not in X.columns:
        X[c] = 0.0
X["opp"] = X["car"].fillna(0) + X["tgt"].fillna(0) + X["att"].fillna(0)
X["w"] = X["position"].map(W).fillna(0.5)
X["proj_role"] = X["proj"]
X["proj"] = X["w"] * X["proj_role"] + (1 - X["w"]) * X["ppg_hist"]

X["bkt"] = pd.cut(X["opp"], bins=BINS, labels=LAB).astype(str)
X["conf"] = X["bkt"].map(CONF).fillna(min(CONF.values()))
X["rel"] = X["position"].map(REL).fillna(0.5)

TEAMS = 10
SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}
FLEX = 2
d = X.sort_values("proj", ascending=False).reset_index(drop=True)
need = {k: v * TEAMS for k, v in SLOTS.items()}
flex_left, started = FLEX * TEAMS, {k: 0 for k in SLOTS}
for _, r in d.iterrows():
    p = r["position"]
    if started[p] < need[p]:
        started[p] += 1
    elif p in ("RB", "WR", "TE") and flex_left > 0:
        started[p] += 1
        flex_left -= 1
REPL = {}
for p, n in started.items():
    v = d[d["position"] == p]["proj"].reset_index(drop=True)
    REPL[p] = float(v.iloc[min(n, len(v) - 1)])

print("\n\n=== REPLACEMENT LEVEL (10 tm, QB/RB/RB/WR/WR/TE/FLEX/FLEX) ===")
for p in ["QB", "RB", "WR", "TE"]:
    print("  %-4s %3d started league-wide   replacement %5.2f ppg" % (p, started[p], REPL[p]))

X["repl"] = X["position"].map(REPL)
X["vorp"] = X["proj"] - X["repl"]
X["value"] = X["vorp"] * X["exp_games"] * X["rel"] * X["conf"]
X = X.sort_values("value", ascending=False).reset_index(drop=True)
X["rk"] = X.index + 1
X["prk"] = X.groupby("position")["value"].rank(ascending=False, method="min").astype(int)
X.to_csv("board_situational.csv", index=False)

print("\n\n%s" % ("=" * 102))
print("TOP 100 BY VALUE   =  VORP x games x reliability x confidence")
print("  proj = %d%%-%d%% blend of role-implied and historical, weights measured above" 
      % (100 * min(W.values()), 100 * max(W.values())))
print("=" * 102)
print("  rk  player                 tm   pos  #   role   hist   proj   repl   vorp    g   conf   VALUE")
print("  " + "-" * 98)
for _, r in X.head(100).iterrows():
    print("  %-3d %-22s %-4s %-3s %2d  %5.1f  %5.1f  %5.1f  %5.1f  %+5.1f %4.1f  %.2f  %6.1f"
          % (r["rk"], str(r["player_name"])[:22], r["team"], r["position"], r["prk"],
             r["proj_role"], r["ppg_hist"], r["proj"], r["repl"], r["vorp"],
             r["exp_games"], r["conf"], r["value"]))

print("\n\n=== WHERE THE VALUE LIVES (your PPR question, answered) ===")
for n in [12, 24, 50, 100]:
    c = X.head(n)["position"].value_counts().to_dict()
    print("  top %3d:  %s" % (n, "   ".join("%s %2d" % (k, c.get(k, 0))
                                            for k in ["WR", "RB", "TE", "QB"])))
print("\n  avg VORP of the top 12 at each position:")
for p in ["WR", "RB", "TE", "QB"]:
    print("    %-4s %+5.2f" % (p, X[X["position"] == p].nlargest(12, "value")["vorp"].mean()))

print("\n\n=== UNPROVEN PLAYERS: WHAT THE BLEND + CONFIDENCE DID ===")
q = X[(X["proj_opp"] > 8) & (X["opp"] < 150)]
print(q.nsmallest(12, "conf")[["player_name", "team", "position", "opp",
                               "proj_role", "ppg_hist", "proj", "conf",
                               "value"]].round(2).to_string(index=False))
print("\nSaved board_situational.csv")
