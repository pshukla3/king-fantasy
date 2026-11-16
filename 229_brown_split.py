import pandas as pd
import numpy as np
import nflreadpy as nfl
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge

F = ["ppg", "cpg", "tpg", "opp_share", "car_share",
     "ypc", "rtdr", "ctch", "g", "age", "draft_pick"]

def rg():
    return Pipeline([
        ("i", SimpleImputer(strategy="median")),
        ("s", StandardScaler()),
        ("m", Ridge(alpha=3.0))])

S = pd.read_csv("pos_season_panel.csv", low_memory=False)
PL = nfl.load_players()
PL = PL.to_pandas() if hasattr(PL, "to_pandas") else PL
idc = "gsis_id" if "gsis_id" in PL.columns else "player_id"
PL = PL[[idc, "display_name", "birth_date",
         "draft_pick"]].rename(
    columns={idc: "player_id"}).drop_duplicates("player_id")
PL["by"] = pd.to_datetime(PL["birth_date"],
                          errors="coerce").dt.year
S = S.merge(PL, on="player_id", how="left")
S["age"] = S["season"] - S["by"]
S["draft_pick"] = S["draft_pick"].fillna(260.0)

NX = S[["player_id", "season", "ppg"]].copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"ppg": "y"})
D = S.merge(NX, on=["player_id", "season"], how="inner")
D = D.dropna(subset=["y", "ppg"])
tr = D[D["position"] == "RB"]
m = rg().fit(tr[F].values, tr["y"].values)
print("RB pairs trained on: %d" % len(tr))

cb = S[(S["season"] == 2025)
       & (S["display_name"].astype(str)
          .str.contains("Chase Brown", na=False))]
assert len(cb), "not found"
cb = cb.iloc[0]

print("\n=== WHAT DRAFT CAPITAL COSTS HIM ===")
print("  same player, same 2025 line, pick varied\n")
print("  %-14s %9s %9s" % ("pick", "proj", "vs actual"))
print("  " + "-" * 34)
base = None
for pk, lab in [(163.0, "163 (his)"), (100.0, "100"),
                (60.0, "60"), (32.0, "32"),
                (10.0, "10"), (2.0, "2")]:
    r = cb.copy()
    r["draft_pick"] = pk
    v = float(m.predict(
        pd.DataFrame([r])[F].values)[0])
    if base is None:
        base = v
    print("  %-14s %9.2f %+9.2f" % (lab, v, v - base))

print("\n=== DECOMPOSING THE -20%% ===")
act = float(cb["ppg"])
r1 = cb.copy()
r1["draft_pick"] = 32.0
top = float(m.predict(pd.DataFrame([r1])[F].values)[0])
print("  2025 actual              %6.2f" % act)
print("  model, as a rd-1 pick    %6.2f  (%+.1f%%)"
      % (top, 100 * (top / act - 1)))
print("  model, at pick 163       %6.2f  (%+.1f%%)"
      % (base, 100 * (base / act - 1)))
print("  " + "-" * 40)
print("  regression to the mean   %+6.2f ppg" % (top - act))
print("  draft capital            %+6.2f ppg" % (base - top))
print("  over 17 games            %+6.0f pts"
      % ((base - top) * 17))
