import json, re, os
import pandas as pd

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

TYP = {}
p25 = "data_usage/snaps_2025.parquet"
if os.path.exists(p25):
    S = pd.read_parquet(p25)
    S["k"] = S["player"].map(norm)
    g = S[S["week"].between(1, 17)].groupby("k")["offense_pct"]
    TYP = {k: float(v) for k, v in g.median().items()
           if pd.notna(v)}
print("players with a 2025 snap baseline: %d" % len(TYP))

CUR = {}
p26 = "data_usage/snaps_2026.parquet"
if os.path.exists(p26):
    S = pd.read_parquet(p26)
    for _, r in S[S["week"] == 1].iterrows():
        try:
            CUR[norm(r["player"])] = float(r["offense_pct"])
        except (TypeError, ValueError):
            pass
print("players with week 1 snaps: %d" % len(CUR))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
W1 = {norm(r["n"]): r
      for r in json.load(open("site/_wk1.json"))["rows"]}

def part(k):
    c = CUR.get(k)
    if c is None:
        return 1.0
    t = TYP.get(k) or 0.70
    if t <= 0.05:
        return 1.0
    return max(0.0, min(1.0, c / t))

rows = []
for _, r in B.iterrows():
    base = r.get("points")
    if pd.isna(base):
        rows.append(None)
        continue
    w1 = W1.get(r["k"])
    if not w1:
        rows.append(round(float(base), 2))
        continue
    lam = float(r.get("lam") or 0.334)
    w = lam * part(r["k"])
    rows.append(round((1 - w) * float(base)
                      + w * float(w1["act"]), 2))
B["part"] = B["k"].map(part).round(3)
B["proj_live"] = rows
B = B.drop(columns=["k"])
B.to_csv("board_final.csv", index=False)

print("\n%-22s %6s %6s %7s %7s %7s"
      % ("PLAYER", "SNAP", "PART", "BASE", "OLD", "NOW"))
for nm in ("Kyler Murray", "Ja'Marr Chase",
           "Derrick Henry", "Jalen Coker",
           "Sam Darnold", "Ashton Jeanty"):
    z = B[B["player_display_name"] == nm]
    for _, r in z.iterrows():
        k = norm(nm)
        print("%-22s %6s %6.2f %7.2f %7s %7.2f"
              % (nm[:22],
                 ("%.0f%%" % (100 * CUR[k])) if k in CUR
                 else "-",
                 r["part"], r["points"], "-",
                 r["proj_live"]))
