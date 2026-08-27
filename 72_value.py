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

S = H.groupby(["player_id", "position", "season"]).agg(
    g=("week", "nunique"), pts=("pts", "sum"), opp=("opp", "sum")).reset_index()
S = S[S["g"] >= 3].copy()
S["ppg"] = S["pts"] / S["g"]

nx = S[["player_id", "season", "ppg", "g"]].copy()
nx["season"] = nx["season"] - 1
nx = nx.rename(columns={"ppg": "ppg_n", "g": "g_n"})
D = S.merge(nx, on=["player_id", "season"], how="inner")
D = D[D["g_n"] >= 8].copy()

BINS = [0, 60, 120, 220, 350, 99999]
LAB = ["<60", "60-120", "120-220", "220-350", "350+"]
D["bkt"] = pd.cut(D["opp"], bins=BINS, labels=LAB)

print("=== IS A SMALL SAMPLE ACTUALLY LESS PREDICTIVE? ===")
print("  bucket = opportunities in the prior season")
print("  r = correlation between his prior ppg and his next-season ppg")
print("  " + "-" * 52)
print("  prior opp       n       r      mean ppg next")
CONF = {}
for b, x in D.groupby("bkt", observed=True):
    if len(x) < 40:
        continue
    r = x["ppg"].corr(x["ppg_n"])
    CONF[str(b)] = max(r, 0.05)
    print("  %-12s %5d   %.3f        %5.1f" % (b, len(x), r, x["ppg_n"].mean()))
mx = max(CONF.values())
CONF = {k: v / mx for k, v in CONF.items()}
print("\n  normalized confidence multipliers: %s"
      % {k: round(v, 3) for k, v in CONF.items()})

REL = {}
for pos, x in D.groupby("position"):
    if len(x) >= 60:
        REL[pos] = x["ppg"].corr(x["ppg_n"])
print("  positional reliability: %s" % {k: round(v, 3) for k, v in REL.items()})

X = pd.read_csv("top100_situational.csv", low_memory=False)
X["bkt"] = pd.cut(X["opp"], bins=BINS, labels=LAB).astype(str)
X["conf_smp"] = X["bkt"].map(CONF).fillna(min(CONF.values()))
X["hist_opg"] = X["opp"] / X["g"].replace(0, np.nan)
X["jump"] = X["proj_opp"] / X["hist_opg"].replace(0, np.nan)
X["conf_jump"] = 1.0 / (1.0 + (X["jump"].fillna(1.0) - 1.0).clip(lower=0) * 0.5)
X["conf"] = X["conf_smp"] * X["conf_jump"]
X["rel"] = X["position"].map(REL).fillna(0.5)

TEAMS = 10
SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}
FLEX = 2
d = X.sort_values("proj", ascending=False).reset_index(drop=True)
need = {k: v * TEAMS for k, v in SLOTS.items()}
flex_left = FLEX * TEAMS
started = {k: 0 for k in SLOTS}
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
    print("  %-4s started league-wide: %3d   replacement ppg %5.2f"
          % (p, started[p], REPL[p]))

X["repl"] = X["position"].map(REPL)
X["vorp"] = X["proj"] - X["repl"]
X["value"] = X["vorp"] * X["exp_games"] * X["rel"] * X["conf"]
X = X.sort_values("value", ascending=False).reset_index(drop=True)
X["rk"] = X.index + 1
X["prk"] = X.groupby("position")["value"].rank(ascending=False, method="min").astype(int)
X.to_csv("board_situational.csv", index=False)

print("\n\n%s" % ("=" * 100))
print("TOP 100 BY VALUE  =  VORP x expected games x reliability x confidence")
print("=" * 100)
print("  rk  player                 tm   pos  #   proj   repl   vorp   g    conf   VALUE")
print("  " + "-" * 96)
for _, r in X.head(100).iterrows():
    print("  %-3d %-22s %-4s %-3s %2d  %5.1f  %5.1f  %+5.1f  %4.1f  %.2f  %6.1f"
          % (r["rk"], str(r["player_name"])[:22], r["team"], r["position"],
             r["prk"], r["proj"], r["repl"], r["vorp"], r["exp_games"],
             r["conf"], r["value"]))

print("\n\n=== WHERE THE VALUE ACTUALLY LIVES (your PPR question) ===")
for n in [12, 24, 50, 100]:
    c = X.head(n)["position"].value_counts().to_dict()
    print("  top %3d:  %s" % (n, "  ".join("%s %d" % (k, c.get(k, 0))
                                           for k in ["WR", "RB", "TE", "QB"])))
print("\n  average VORP of the top 12 at each position:")
for p in ["WR", "RB", "TE", "QB"]:
    v = X[X["position"] == p].nlargest(12, "value")["vorp"].mean()
    print("    %-4s %+5.2f" % (p, v))

print("\n\n=== MOST DISCOUNTED FOR UNCERTAINTY ===")
q = X[X["proj_opp"] > 8]
print(q.nsmallest(12, "conf")[["player_name", "team", "position", "opp", "hist_opg",
                               "proj_opp", "proj", "conf", "value"]].round(2).to_string(index=False))
print("\nSaved board_situational.csv")
