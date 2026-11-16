import glob, re
import numpy as np
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

SEASONS = [2023, 2024, 2025]
I = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_inj/inj_*.parquet"))],
              ignore_index=True)
I["season"] = I["season"].astype(int)
I = I[I["season"].isin(SEASONS)]
NM = next(c for c in ("full_name", "player_name",
                      "player_display_name")
          if c in I.columns)
I["k"] = I[NM].map(norm)
OUT = {"out", "injured reserve", "doubtful"}
I["missed"] = I["report_status"].astype(str)\
    .str.lower().isin(OUT)
print("injury rows %d | flagged as missed %d"
      % (len(I), int(I["missed"].sum())))

# weeks missed per player-season
M = (I[I["missed"]]
     .groupby(["k", "season"])["week"].nunique()
     .reset_index().rename(columns={"week": "missed"}))

# denominator: only seasons the player was actually active
W = pd.read_parquet("weekly_all.parquet")
W = W[W["season"].isin(SEASONS)]
W["k"] = W["player_display_name"].map(norm)
ACT = (W.groupby(["k", "season"])["week"].nunique()
       .reset_index().rename(columns={"week": "played"}))
def _md(x):
    m = x.dropna().mode()
    return m.iloc[0] if len(m) else ""
POSN = W.groupby("k")["position"].agg(_md)

D = ACT.merge(M, on=["k", "season"], how="left")
D["missed"] = D["missed"].fillna(0.0)
D = D[D["played"] + D["missed"] >= 4]
D["rate"] = D["missed"] / (D["played"] + D["missed"])
D["pos"] = D["k"].map(POSN)
SKILL = ["QB", "RB", "WR", "TE"]
pm = D[D["pos"].isin(SKILL)].groupby("pos")["rate"]\
    .mean().to_dict()
print("\nmean share of weeks missed to injury:")
for p in SKILL:
    print("   %-4s %.1f%%" % (p, 100 * pm.get(p, 0)))

agg = D.groupby(["k", "pos"])["rate"]\
    .agg(["mean", "count"]).reset_index()
K = 1.5
RISK = {}
for _, r in agg.iterrows():
    base = pm.get(r["pos"], 0.12)
    n = r["count"]
    v = (r["mean"] * n + base * K) / (n + K)
    RISK[r["k"]] = (round(float(v), 3), int(n))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
B["inj_risk"] = B["k"].map(
    lambda k: (RISK.get(k) or (None, 0))[0])
B["risk_n"] = B["k"].map(
    lambda k: (RISK.get(k) or (None, 0))[1])
for p in SKILL:
    m = (B["position"] == p) & B["inj_risk"].isna()
    B.loc[m, "inj_risk"] = round(float(pm.get(p, 0.12)), 3)
B["exp_g"] = (17.0 * (1.0 - B["inj_risk"])).round(1)
B = B.drop(columns=["k"])
B.to_csv("board_final.csv", index=False)
print("\ncoverage: %d of %d have measured history"
      % (int((B["risk_n"] > 0).sum()), len(B)))

z = B.sort_values("vorp", ascending=False).head(60)
print("\n=== HIGHEST RISK IN TOP 60 BY VORP ===")
for _, r in z.sort_values("inj_risk",
                          ascending=False).head(10).iterrows():
    print("  %-24s %-4s %4.0f%%  exp games %4.1f  (%d yrs)"
          % (r["player_display_name"][:24], r["position"],
             100 * r["inj_risk"], r["exp_g"], r["risk_n"]))
print("\n=== LOWEST RISK IN TOP 60 ===")
for _, r in z.sort_values("inj_risk").head(6).iterrows():
    print("  %-24s %-4s %4.0f%%  exp games %4.1f  (%d yrs)"
          % (r["player_display_name"][:24], r["position"],
             100 * r["inj_risk"], r["exp_g"], r["risk_n"]))
