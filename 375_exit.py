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

I = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_inj/inj_*.parquet"))],
              ignore_index=True)
NM = next(c for c in ("full_name", "player_name",
                      "player_display_name")
          if c in I.columns)
I["k"] = I[NM].map(norm)
I["season"] = I["season"].astype(int)
I["week"] = I["week"].astype(int)
OUT = {"out", "injured reserve", "doubtful"}
I["bad"] = I["report_status"].astype(str)\
    .str.lower().isin(OUT)
HURT = set(zip(I[I["bad"]]["season"], I[I["bad"]]["week"],
               I[I["bad"]]["k"]))
print("player-weeks listed out/IR/doubtful: %d" % len(HURT))

rows = []
for (sea, k), d in W.groupby(["season", "k"]):
    w1 = d[d["week"] == 1]["fp"]
    rest = d[d["week"].between(2, 17)]["fp"]
    if not len(w1) or len(rest) < 6:
        continue
    prev = W[(W["season"] == sea - 1) & (W["k"] == k)]["fp"]
    if len(prev) < 6:
        continue
    # hurt in the game = listed out in week 2 or 3
    exit_ = ((sea, 2, k) in HURT) or ((sea, 3, k) in HURT)
    rows.append({"prior": float(prev.mean()),
                 "wk1": float(w1.iloc[0]),
                 "rest": float(rest.mean()),
                 "exit": bool(exit_)})
D = pd.DataFrame(rows)
print("week-1 results followed by an out/IR listing: "
      "%d of %d (%.0f%%)"
      % (int(D["exit"].sum()), len(D),
         100 * D["exit"].mean()))

def lam(d):
    X = np.column_stack([d["prior"], d["wk1"],
                         np.ones(len(d))])
    b = np.linalg.lstsq(X, d["rest"].values,
                        rcond=None)[0]
    return b[1] / (b[0] + b[1])

print("\n=== SHOULD AN INJURY-EXIT GAME COUNT? ===")
for lab, d in (("healthy after", D[~D["exit"]]),
               ("hurt after", D[D["exit"]])):
    if len(d) < 50:
        continue
    r = np.corrcoef(d["wk1"], d["rest"])[0, 1]
    print("  %-14s n=%-5d weight %.3f  corr %.3f"
          % (lab, len(d), lam(d), r))

print("\n=== AMONG LOW-SCORING WEEK 1s ONLY ===")
lo = D[D["wk1"] < D["prior"] * 0.5]
for lab, d in (("healthy after", lo[~lo["exit"]]),
               ("hurt after", lo[lo["exit"]])):
    if len(d) < 30:
        continue
    print("  %-14s n=%-5d  rest-of-season ppg %.2f "
          "vs prior %.2f (%+.2f)"
          % (lab, len(d), d["rest"].mean(),
             d["prior"].mean(),
             d["rest"].mean() - d["prior"].mean()))
