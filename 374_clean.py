import glob, re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

W = pd.read_parquet("weekly_all.parquet")
if "season_type" in W.columns:
    W = W[W["season_type"] == "REG"]
W["k"] = W["player_display_name"].map(norm)
W["fp"] = pd.to_numeric(W["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
W = W[W["week"] <= 17]

S = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_usage/snaps_2*.parquet"))],
              ignore_index=True)
S["k"] = S["player"].map(norm)
S["pct"] = pd.to_numeric(
    S["offense_pct"].astype(str).str.rstrip("%"),
    errors="coerce")
if S["pct"].max() > 1.5:
    S["pct"] = S["pct"] / 100.0
# a player's typical snap share that season
TYP = (S[S["week"].between(2, 17)]
       .groupby(["season", "k"])["pct"].median()
       .rename("typ").reset_index())
S1 = S[S["week"] == 1][["season", "k", "pct"]]
S1 = S1.merge(TYP, on=["season", "k"], how="left")
S1["clean"] = (S1["pct"] >= 0.6 * S1["typ"]) \
    & (S1["pct"] >= 0.35)
print("week-1 rows with snaps: %d | clean: %d (%.0f%%)"
      % (len(S1), int(S1["clean"].sum()),
         100 * S1["clean"].mean()))

rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    w1 = d[d["week"] == 1]["fp"]
    rest = d[d["week"].between(2, 17)]["fp"]
    if not len(w1) or len(rest) < 6:
        continue
    prev = W[(W["season"] == sea - 1) & (W["k"] == k)]["fp"]
    if len(prev) < 6:
        continue
    rows.append({"season": sea, "k": k,
                 "prior": float(prev.mean()),
                 "wk1": float(w1.iloc[0]),
                 "rest": float(rest.mean())})
D = pd.DataFrame(rows).merge(
    S1[["season", "k", "clean", "pct", "typ"]],
    on=["season", "k"], how="left")

def lam(d):
    X = np.column_stack([d["prior"], d["wk1"],
                         np.ones(len(d))])
    b = np.linalg.lstsq(X, d["rest"].values,
                        rcond=None)[0]
    return b[1] / (b[0] + b[1]), len(d)

print("\n=== HOW MUCH SHOULD WEEK 1 COUNT? ===")
a, n = lam(D.dropna(subset=["wk1"]))
print("  all games            n=%-5d weight %.3f" % (n, a))
c = D[D["clean"] == True]
a2, n2 = lam(c)
print("  clean games only     n=%-5d weight %.3f"
      % (n2, a2))
t = D[D["clean"] == False]
if len(t) > 80:
    a3, n3 = lam(t)
    print("  truncated games      n=%-5d weight %.3f"
          % (n3, a3))

print("\n=== DOES A TRUNCATED WEEK 1 PREDICT ANYTHING? ===")
for lab, d in (("clean", c), ("truncated", t)):
    if len(d) < 80:
        continue
    r = np.corrcoef(d["wk1"], d["rest"])[0, 1]
    print("  %-10s n=%-5d corr(week1, rest) = %.3f"
          % (lab, len(d), r))
