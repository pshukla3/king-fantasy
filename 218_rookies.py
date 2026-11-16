import json
import re
import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(d):
    return d.to_pandas() if hasattr(d, "to_pandas") else d

SUF = re.compile(r"\b(jr|sr|ii|iii|iv)\b")
FIX = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX",
       "AZ": "ARI"}

def key(s):
    s = re.sub(r"[^a-z ]", " ", str(s).lower())
    return re.sub(r"\s+", "", SUF.sub(" ", s))

S = pd.read_csv("pos_season_panel.csv", low_memory=False)
print("panel columns: %s" % sorted(S.columns.tolist()))

PJ = json.load(open("sleeper_players_fresh.json"))
rows = []
for d in PJ.values():
    if not d.get("team"):
        continue
    if d.get("position") not in ("RB", "WR", "TE"):
        continue
    tm = FIX.get(d["team"], d["team"])
    rows.append({"k": key(d.get("full_name")),
                 "nm": d.get("full_name"),
                 "ps": d["position"], "tm": tm,
                 "dco": d.get("depth_chart_order"),
                 "dcp": d.get("depth_chart_position"),
                 "yexp": d.get("years_exp")})
SL = pd.DataFrame(rows).drop_duplicates(["k", "ps"])
print("\nlive skill players with a team: %d" % len(SL))
print("  with a depth-chart order: %d"
      % int(SL["dco"].notna().sum()))

PL = pl(nfl.load_players())
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
PL = PL[[idc, "display_name", "draft_pick",
         "draft_round"]].rename(
    columns={idc: "player_id"})
PL["k"] = PL["display_name"].apply(key)
PL = PL.drop_duplicates("k")[["k", "player_id",
                              "draft_pick", "draft_round"]]
SL = SL.merge(PL, on="k", how="left")

RK = SL[SL["yexp"] == 0].copy()
RK["pick"] = RK["draft_pick"].fillna(260.0)
print("\n=== 2026 ROOKIES (RB/WR/TE) ===")
print("  count: %d" % len(RK))
print(RK.groupby("ps").size().to_string())

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
CUR = dict(zip(B["k"], B["pp"]))
RK["cur"] = RK["k"].map(CUR)

print("\n=== WHAT THEY CARRY NOW ===")
print("  %-24s %-4s %-4s %5s %5s %8s"
      % ("player", "pos", "tm", "pick", "dpth", "cur ppg"))
print("  " + "-" * 56)
for _, r in RK.sort_values("pick").head(25).iterrows():
    print("  %-24s %-4s %-4s %5s %5s %8s"
          % (str(r["nm"])[:24], r["ps"], r["tm"],
             "UDFA" if r["pick"] >= 260 else "%.0f" % r["pick"],
             "--" if r["dco"] != r["dco"] else "%.0f" % r["dco"],
             "--" if r["cur"] != r["cur"] else "%.2f" % r["cur"]))
for p in ["RB", "WR", "TE"]:
    d = RK[RK["ps"] == p]["cur"].dropna()
    if len(d):
        print("  %-3s n=%-3d %d unique values"
              % (p, len(d), d.nunique()))
RK.to_csv("rookies_2026.csv", index=False)

print("\n" + "=" * 58)
print("=== WHAT DOES DRAFT CAPITAL BUY IN SHARE? ===")
PLR = pl(nfl.load_players())
idc2 = "gsis_id" if "gsis_id" in PLR.columns else "player_id"
PLR = PLR[[idc2, "draft_pick", "rookie_season"]].rename(
    columns={idc2: "player_id"}).drop_duplicates("player_id")
H = S.merge(PLR, on="player_id", how="left")
H = H[H["season"] == H["rookie_season"]].copy()
H["pick"] = H["draft_pick"].fillna(260.0)
H["lp"] = np.log(H["pick"].clip(lower=1))
SHC = {"RB": "opp_share", "WR": "tar_share",
       "TE": "tar_share"}

CUT = 2021
FIT = {}
print("  share = rookie's cut of his team's opportunity")
print("  %-4s %5s %5s %9s %9s %8s"
      % ("pos", "ntr", "nte", "flat MAE", "slot MAE", "gain"))
print("  " + "-" * 48)
for p in ["RB", "WR", "TE"]:
    c = SHC[p]
    d = H[(H["position"] == p) & H[c].notna()]
    tr = d[d["season"] < CUT]
    te = d[d["season"] >= CUT]
    if len(tr) < 30 or len(te) < 10:
        print("  %-4s too few rows (%d/%d)"
              % (p, len(tr), len(te)))
        continue
    fl = float(tr[c].mean())
    b = tr["lp"].cov(tr[c]) / tr["lp"].var()
    a = tr[c].mean() - b * tr["lp"].mean()
    e0 = (fl - te[c]).abs().mean()
    e1 = ((a + b * te["lp"]) - te[c]).abs().mean()
    FIT[p] = (a, b, fl, e1 < e0)
    print("  %-4s %5d %5d %9.4f %9.4f %+7.1f%%"
          % (p, len(tr), len(te), e0, e1,
             100 * (1 - e1 / e0)))
    print("       %s | pick 10 -> %.3f | pick 60 -> %.3f"
          " | UDFA -> %.3f"
          % ("USE DRAFT SLOT" if e1 < e0 else "USE FLAT",
             a + b * np.log(10), a + b * np.log(60),
             a + b * np.log(260)))

print("\n=== ROOKIE EFFICIENCY (per opportunity) ===")
EFF = {}
for p in ["RB", "WR", "TE"]:
    d = H[H["position"] == p]
    v = float((d["ppg"] / d[SHC[p]].replace(0, np.nan)
               ).replace([np.inf, -np.inf], np.nan)
              .median())
    EFF[p] = v
    print("  %-4s %.2f ppg per 1.00 share (n=%d)"
          % (p, v, len(d)))
print("\n  so ppg = share x this. it is a median so one")
print("  freak rookie season cannot drag the whole class")

print("\n" + "=" * 58)
print("=== HOW MUCH OPPORTUNITY IS ACTUALLY OPEN? ===")
T26 = dict(zip(B.drop_duplicates("player_id")["player_id"],
               B.drop_duplicates("player_id")["team"]))
V = S[S["season"] == 2025].copy()
V["t26"] = V["player_id"].map(T26)
V = V[V["t26"].notna()]
RET = V.groupby(["t26", "position"]).agg(
    ret_tar=("tar_share", "sum"),
    ret_opp=("opp_share", "sum")).reset_index()
TV = (S[S["season"] == 2025][["team", "t_tpg", "t_cpg"]]
      .drop_duplicates("team"))

rows = []
for tm in sorted(set(RET["t26"])):
    d = RET[RET["t26"] == tm]
    rt = float(d[d["position"].isin(["WR", "TE"])]
               ["ret_tar"].sum())
    ro = float(d[d["position"] == "RB"]["ret_opp"].sum())
    rows.append({"tm": tm, "ret_tar": rt, "ret_opp": ro,
                 "open_tar": max(0.0, 1.0 - rt),
                 "open_opp": max(0.0, 1.0 - ro)})
OP = pd.DataFrame(rows)
OP.to_csv("team_opportunity_2026.csv", index=False)
print("  share of 2025 target volume held by")
print("  pass-catchers STILL on the team in 2026\n")
print("  %-5s %10s %10s" % ("tm", "returning", "OPEN"))
print("  " + "-" * 28)
for _, r in OP.sort_values("open_tar",
                           ascending=False).head(10).iterrows():
    print("  %-5s %9.1f%% %9.1f%%"
          % (r["tm"], 100 * r["ret_tar"],
             100 * r["open_tar"]))
print("  ...")
for _, r in OP.sort_values("open_tar").head(5).iterrows():
    print("  %-5s %9.1f%% %9.1f%%"
          % (r["tm"], 100 * r["ret_tar"],
             100 * r["open_tar"]))
print("\n  high OPEN = vacated targets a rookie can win")
print("  low OPEN  = crowded room, rookie has to displace")

print("\n" + "=" * 58)
print("=== 2026 ROOKIE PROJECTIONS ===")
DEPTH = {1: 1.30, 2: 1.00, 3: 0.65, 4: 0.40}
OPM = dict(zip(OP["tm"], OP["open_tar"]))
OOM = dict(zip(OP["tm"], OP["open_opp"]))

out = []
for _, r in RK.iterrows():
    p = r["ps"]
    if p not in FIT:
        continue
    a, b, fl, use = FIT[p]
    base = (a + b * np.log(max(r["pick"], 1))) if use else fl
    base = max(base, 0.005)
    dco = r["dco"]
    dm = DEPTH.get(int(dco), 0.30) if dco == dco else 0.60
    opn = (OOM if p == "RB" else OPM).get(r["tm"], 0.30)
    cap = max(opn, 0.05)
    share = min(base * dm, cap)
    out.append({"nm": r["nm"], "ps": p, "tm": r["tm"],
                "pick": r["pick"], "dco": dco,
                "base": base, "dmult": dm, "open": opn,
                "share": share,
                "proj": round(share * EFF[p], 2),
                "cur": r["cur"]})
O = pd.DataFrame(out).sort_values("proj", ascending=False)
O.to_csv("rookie_proj_2026.csv", index=False)

print("  %-22s %-3s %-4s %5s %4s %6s %6s %6s %6s"
      % ("player", "ps", "tm", "pick", "dep", "share",
         "open", "NEW", "cur"))
print("  " + "-" * 72)
for _, r in O.head(30).iterrows():
    print("  %-22s %-3s %-4s %5s %4s %6.3f %6.2f"
          " %6.2f %6s"
          % (str(r["nm"])[:22], r["ps"], r["tm"],
             "UDFA" if r["pick"] >= 260
             else "%.0f" % r["pick"],
             "--" if r["dco"] != r["dco"]
             else "%.0f" % r["dco"],
             r["share"], r["open"], r["proj"],
             "--" if r["cur"] != r["cur"]
             else "%.2f" % r["cur"]))
print("\n  wrote rookie_proj_2026.csv (%d players)" % len(O))
print("\n  WHAT IS MEASURED vs ASSUMED:")
print("    share ~ draft pick   MEASURED on holdout")
print("    ppg per share        MEASURED, median")
print("    open opportunity     MEASURED from 2025 usage")
print("    depth multipliers    ASSUMED - no historical")
print("      depth charts exist to validate against")
