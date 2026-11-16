import json
import re
import numpy as np
import pandas as pd

SUF = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b")

def key(n):
    s = str(n).lower().replace(".", " ").replace("'", "")
    s = SUF.sub(" ", s)
    return re.sub(r"[^a-z]", "", s)

FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS", "JAC": "JAX"}
SKILL = ["QB", "RB", "WR", "TE", "K"]

PJ = json.load(open("sleeper_players.json"))
rows = []
for sid, d in PJ.items():
    tm, ps, nm = d.get("team"), d.get("position"), d.get("full_name")
    if not tm or not ps or not nm:
        continue
    rows.append({"sid": sid, "nm": nm, "ps": ps,
                 "tm": FIX.get(str(tm).upper(), str(tm).upper())})
U = pd.DataFrame(rows)
print("sleeper players with an NFL team: %d" % len(U))
print("\n=== BY POSITION ===")
print(U.groupby("ps").size().sort_values(
    ascending=False).to_string())

S = U[U["ps"].isin(SKILL)].copy()
print("\nfantasy-eligible QB/RB/WR/TE/K: %d" % len(S))
c = S.groupby("tm").size()
print("teams %d | min %d | max %d | mean %.1f"
      % (len(c), c.min(), c.max(), c.mean()))

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
have = set(zip(B["k"], B["position"].astype(str)))
S["k"] = S["nm"].apply(key)
S["on"] = [(a, b) in have
           for a, b in zip(S["k"], S["ps"])]
print("\n=== COVERAGE vs CURRENT BOARD ===")
print("  on board %d | MISSING %d"
      % (int(S["on"].sum()), int((~S["on"]).sum())))
print(S[~S["on"]].groupby("ps").size().to_string())
S.to_csv("nfl_universe.csv", index=False)
print("\nwrote nfl_universe.csv")

import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"].astype(str), SC["value"]))
MISS = []

def sv(k, d=0.0):
    if k not in V:
        MISS.append(k)
    return float(V.get(k, d))

W = pl(nfl.load_player_stats(seasons=[2023, 2024, 2025]))
NEED = ["passing_yards", "passing_tds",
        "passing_interceptions", "rushing_yards",
        "rushing_tds", "receptions", "receiving_yards",
        "receiving_tds", "sack_fumbles_lost",
        "rushing_fumbles_lost", "receiving_fumbles_lost",
        "fg_made_0_19", "fg_made_20_29", "fg_made_30_39",
        "fg_made_40_49", "fg_made_50_59", "fg_made_60_",
        "fg_missed", "pat_made", "pat_missed"]
for c in NEED:
    if c not in W.columns:
        W[c] = 0.0
    W[c] = pd.to_numeric(W[c], errors="coerce").fillna(0.0)

W["fp"] = (W["passing_yards"] * sv("pass_yd", 0.04)
           + W["passing_tds"] * sv("pass_td", 4.0)
           + W["passing_interceptions"] * sv("pass_int", -2.0)
           + W["rushing_yards"] * sv("rush_yd", 0.1)
           + W["rushing_tds"] * sv("rush_td", 6.0)
           + W["receptions"] * sv("rec", 1.0)
           + W["receiving_yards"] * sv("rec_yd", 0.1)
           + W["receiving_tds"] * sv("rec_td", 6.0)
           + (W["sack_fumbles_lost"]
              + W["rushing_fumbles_lost"]
              + W["receiving_fumbles_lost"])
           * sv("fum_lost", -2.0)
           + (W["fg_made_0_19"] + W["fg_made_20_29"])
           * sv("fgm_20_29", 3.0)
           + W["fg_made_30_39"] * sv("fgm_30_39", 3.0)
           + W["fg_made_40_49"] * sv("fgm_40_49", 4.0)
           + (W["fg_made_50_59"] + W["fg_made_60_"])
           * sv("fgm_50p", 5.0)
           + W["fg_missed"] * sv("fgmiss", -1.0)
           + W["pat_made"] * sv("xpm", 1.0)
           + W["pat_missed"] * sv("xpmiss", -1.0))

print("=== SCORING KEYS DEFAULTED (not in your file) ===")
print("  %s" % (sorted(set(MISS)) or "none"))

H = W.groupby(["player_id", "season"]).agg(
    fp=("fp", "sum"), g=("week", "nunique")).reset_index()
H = H[H["g"] > 0]
PLY = pl(nfl.load_players())
idc = "gsis_id" if "gsis_id" in PLY.columns else "player_id"
PLY = PLY[[idc, "display_name", "position"]].rename(
    columns={idc: "player_id"})
H = H.merge(PLY, on="player_id", how="left")
H["k"] = H["display_name"].apply(key)

DEC = 0.5
H["w"] = DEC ** (2025 - H["season"])
A = H.groupby(["k", "position"]).apply(
    lambda d: pd.Series({
        "wfp": float((d["w"] * d["fp"]).sum()),
        "wg": float((d["w"] * d["g"]).sum()),
        "gms": float(d["g"].sum())}),
    include_groups=False).reset_index()
A["hist"] = A["wfp"] / A["wg"].replace(0, np.nan)
A.to_csv("hist_ppg_by_name.csv", index=False)
print("\nplayers with 2023-25 history: %d" % len(A))
for p in SKILL:
    d = A[A["position"] == p]
    print("  %-4s %5d | median %.2f ppg"
          % (p, len(d), d["hist"].median()))

BASE = {}
for p in SKILL:
    d = B[B["position"] == p].copy()
    d["pp"] = pd.to_numeric(d["points"], errors="coerce")
    d = d[d["pp"].notna()].sort_values("pp", ascending=False)
    lo = d["pp"].iloc[49:100]
    BASE[p] = float(lo.mean()) if len(lo) else float(
        d["pp"].median())
print("=== DEEP-BENCH BASELINE BY POSITION ===")
for p in SKILL:
    print("  %-4s %.2f ppg" % (p, BASE[p]))

KP = 10.0
HM = {(r["k"], r["position"]): (r["hist"], r["gms"])
      for _, r in A.iterrows()}

M = S[~S["on"]].copy()
add, t1, t2 = [], 0, 0
TPL = {}
for p in SKILL:
    d = B[B["position"] == p]
    if len(d):
        TPL[p] = d.iloc[0].to_dict()

for _, r in M.iterrows():
    p = r["ps"]
    if p not in TPL:
        continue
    h, g = HM.get((r["k"], p), (np.nan, 0.0))
    b = BASE[p]
    if h == h and g > 0:
        proj = (h * g + b * KP) / (g + KP)
        src = "history"
        t2 += 1
    else:
        proj = b * 0.5
        src = "baseline"
        t1 += 1
    d = dict(TPL[p])
    d["player_id"] = "SLP_%s" % r["sid"]
    d["player_display_name"] = r["nm"]
    d["position"] = p
    d["team"] = r["tm"]
    d["points"] = round(float(max(proj, 0.0)), 2)
    d["exp_games"] = 17.0
    d["status"] = np.nan
    d["depth_rank"] = np.nan
    d["adp"] = np.nan
    d["games_mult"] = 1.0
    d["points_mult"] = 1.0
    d["source"] = src
    add.append(d)

print("\n=== ADDING ===")
print("  from 2023-25 history : %d" % t2)
print("  baseline only        : %d" % t1)
print("  total new rows       : %d" % len(add))

B2 = B.drop(columns=["k"])
B2 = pd.concat([B2, pd.DataFrame(add)], ignore_index=True)
B2.to_csv("board_final.csv", index=False)
print("\nboard %d -> %d rows" % (len(B), len(B2)))
print(B2.groupby("position").size().to_string())

B2["k"] = B2["player_display_name"].apply(key)
have2 = set(zip(B2["k"], B2["position"].astype(str)))
left = [(a, b) for a, b in zip(S["k"], S["ps"])
        if (a, b) not in have2]
print("\nfantasy-eligible players still unmapped: %d"
      % len(left))
assert len(left) == 0, left[:10]
print("OK - every rostered skill player is on the board")
