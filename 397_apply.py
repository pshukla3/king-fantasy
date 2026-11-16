import os, re, ssl, certifi, pickle, glob
import urllib.request as U
import numpy as np
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
R = ("https://github.com/nflverse/nflverse-data/releases/"
     "download/stats_player/stats_player_week_2026.parquet")
P = "data_usage/wk_2026.parquet"
if not os.path.exists(P):
    try:
        open(P, "wb").write(U.urlopen(
            U.Request(R, headers=H), timeout=90,
            context=CTX).read())
        print("downloaded 2026 weekly stats")
    except Exception as e:
        print("2026 nflverse not available:", str(e)[:50])

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

if not os.path.exists(P):
    raise SystemExit("need 2026 weekly data to proceed")

N = pd.read_parquet(P)
if "season_type" in N.columns:
    N = N[N["season_type"] == "REG"]
N = N[N["position"].isin(["QB", "RB", "WR", "TE"])].copy()
N["k"] = N["player_display_name"].map(norm)
N["fp"] = pd.to_numeric(N["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
print("2026 rows: %d | weeks %s"
      % (len(N), sorted(N["week"].unique())))

for c in ("targets", "carries", "target_share",
          "air_yards_share", "wopr"):
    if c in N.columns:
        N[c] = pd.to_numeric(N[c], errors="coerce")\
            .fillna(0.0)
    else:
        N[c] = 0.0

S = pd.concat([pd.read_parquet(f) for f in
               sorted(glob.glob("data_usage/snaps_2026*.parquet"))],
              ignore_index=True) \
    if glob.glob("data_usage/snaps_2026*.parquet") \
    else pd.DataFrame(columns=["player", "week",
                               "offense_pct"])
if len(S):
    S["k"] = S["player"].map(norm)
    S["snap"] = pd.to_numeric(S["offense_pct"],
                              errors="coerce")
    N = N.merge(S[["week", "k", "snap"]],
                on=["week", "k"], how="left")
else:
    N["snap"] = np.nan

tm = N.groupby(["week", "team"]).agg(
    tm_tgt=("targets", "sum"),
    tm_car=("carries", "sum")).reset_index()
N = N.merge(tm, on=["week", "team"], how="left")
N["tgt_share"] = N["targets"] / N["tm_tgt"].clip(lower=1)
N["car_share"] = N["carries"] / N["tm_car"].clip(lower=1)

O = pd.read_parquet("weekly_all.parquet")
O["k"] = O["player_display_name"].map(norm)
O["fp"] = pd.to_numeric(O["fantasy_points_ppr"],
                        errors="coerce").fillna(0.0)
PY = (O[O["season"] == 2025].groupby("k")["fp"]
      .mean().to_dict())

N = N.sort_values(["k", "week"])
g = N.groupby("k")
agg = []
for k, d in g:
    d = d.sort_values("week")
    row = {"k": k,
           "n": d["player_display_name"].iloc[-1],
           "position": d["position"].iloc[-1],
           "team": d["team"].iloc[-1],
           "r3_fp": d["fp"].mean(),
           # training uses min_periods=2 for the 8-game
           # window; with one game it must stay NaN so the
           # model leans on prior-season form instead
           "r8_fp": (d["fp"].mean() if len(d) >= 2
                     else np.nan),
           "r8_snap": (d["snap"].mean() if len(d) >= 2
                       else np.nan),
           "prev_fp": d["fp"].iloc[-1],
           "py_fp": PY.get(k, np.nan),
           "r3_tgt": d["targets"].mean(),
           "r3_car": d["carries"].mean(),
           "r3_snap": d["snap"].mean(),
           "r3_tgts": d["tgt_share"].mean(),
           "r3_cars": d["car_share"].mean(),
           "opp_allow": 25.0,
           "gm_no": len(d),
           "r3_wopr": d["wopr"].mean(),
           "r3_ays": d["air_yards_share"].mean(),
           "r3_ts": d["target_share"].mean()}
    agg.append(row)
F = pd.DataFrame(agg)
for p in ("QB", "RB", "WR", "TE"):
    F["is_" + p] = (F["position"] == p).astype(int)
print("players with 2026 data: %d" % len(F))

B = pickle.load(open("ros_model.pkl", "rb"))
M, FE = B["model"], B["features"]
for c in FE:
    if c not in F.columns:
        F[c] = np.nan
F["proj_model"] = M.predict(F[FE]).round(2)
F = F.sort_values("proj_model", ascending=False)
F[["k", "n", "position", "team", "proj_model",
   "r3_snap", "r3_ts", "gm_no"]].to_csv(
    "model_proj.csv", index=False)
print("wrote model_proj.csv")

print("\n=== TOP 40 BY MODEL PROJECTION ===")
print("%-3s %-24s %-4s %-4s %7s %6s %6s"
      % ("#", "PLAYER", "POS", "TM", "PROJ", "SNAP", "TS"))
for i, (_, r) in enumerate(F.head(40).iterrows(), 1):
    print("%-3d %-24s %-4s %-4s %7.2f %6s %6s"
          % (i, r["n"][:24], r["position"], r["team"],
             r["proj_model"],
             "-" if pd.isna(r["r3_snap"])
             else "%.0f%%" % (100 * r["r3_snap"]),
             "-" if pd.isna(r["r3_ts"])
             else "%.2f" % r["r3_ts"]))
