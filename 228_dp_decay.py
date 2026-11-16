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
PL = PL[[idc, "birth_date", "draft_pick"]].rename(
    columns={idc: "player_id"}).drop_duplicates("player_id")
PL["by"] = pd.to_datetime(PL["birth_date"],
                          errors="coerce").dt.year
S = S.merge(PL[["player_id", "by", "draft_pick"]],
            on="player_id", how="left")
S["age"] = S["season"] - S["by"]
S["draft_pick"] = S["draft_pick"].fillna(260.0)
S = S.sort_values(["player_id", "season"])
S["exp"] = S.groupby("player_id").cumcount()

NX = S[["player_id", "season", "ppg"]].copy()
NX["season"] = NX["season"] - 1
NX = NX.rename(columns={"ppg": "y"})
D = S.merge(NX, on=["player_id", "season"], how="inner")
D["ls"] = D["season"] + 1
D = D.dropna(subset=["y", "ppg"])
print("pairs: %d | seasons %d-%d"
      % (len(D), D["ls"].min(), D["ls"].max()))
print(D.groupby("position").size().to_string())

TEST = [2022, 2023, 2024, 2025]

def wf(pos, cols):
    out = []
    for T in TEST:
        tr = D[(D["position"] == pos) & (D["ls"] < T)]
        te = D[(D["position"] == pos) & (D["ls"] == T)]
        if len(te) < 20:
            continue
        m = rg().fit(tr[cols].values, tr["y"].values)
        p = m.predict(te[cols].values)
        z = te[["exp", "draft_pick"]].copy()
        z["e"] = np.abs(p - te["y"].values)
        out.append(z)
    return pd.concat(out, ignore_index=True)

NO = [c for c in F if c != "draft_pick"]
print("\n=== DOES DRAFT CAPITAL STILL PAY OFF? ===")
print("  MAE on holdout years, with vs without it")
print("  split by how many prior seasons he had\n")
print("  %-4s %-10s %5s %8s %8s %8s"
      % ("pos", "group", "n", "with dp", "no dp", "gain"))
print("  " + "-" * 50)
for pos in ["RB", "WR", "TE"]:
    a = wf(pos, F)
    b = wf(pos, NO)
    for lab, msk in [("exp 0-1", a["exp"] <= 1),
                     ("exp 2+", a["exp"] >= 2),
                     ("exp 3+", a["exp"] >= 3)]:
        x = float(a[msk]["e"].mean())
        y = float(b[msk.values]["e"].mean())
        print("  %-4s %-10s %5d %8.4f %8.4f %+7.2f%%"
              % (pos, lab, int(msk.sum()), x, y,
                 100.0 * (1 - x / y)))
    print()
print("  positive gain = draft capital EARNS its keep")
print("  negative gain = it is hurting that group")
