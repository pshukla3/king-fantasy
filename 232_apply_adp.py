import pandas as pd
import numpy as np
import json
import re

W = 0.20
OVER = {}
# to force Jefferson to WR5, uncomment:
# OVER[("justinjefferson", "WR")] = 5

def key(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

J = json.load(open("sleeper_proj_raw.json"))
rows = []
for d in J:
    p = d.get("player") or {}
    st = d.get("stats") or {}
    a = st.get("adp_ppr")
    if a is None or float(a) >= 999:
        continue
    nm = (str(p.get("first_name", "")) + " "
          + str(p.get("last_name", ""))).strip()
    rows.append({"k": key(nm),
                 "position": p.get("position"),
                 "sadp": float(a)})
A = pd.DataFrame(rows).sort_values("sadp")
A = A.drop_duplicates(["k", "position"])

import os
SRC = ("board_pre_adp.csv"
       if os.path.exists("board_pre_adp.csv")
       else "board_final.csv")
print("source board: %s" % SRC)
B = pd.read_csv(SRC, low_memory=False)
B["k"] = B["player_display_name"].apply(key)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
if "sadp" in B.columns:
    B = B.drop(columns=["sadp"])
B = B.merge(A, on=["k", "position"], how="left")
print("blend weight on MODEL: %.2f" % W)
print("rows with Sleeper ADP: %d of %d"
      % (int(B["sadp"].notna().sum()), len(B)))

NEW = {}
for p in ["RB", "WR", "TE"]:
    d = B[(B["position"] == p) & (B["pp"] > 0)
          & B["sadp"].notna()].copy()
    if len(d) < 5:
        continue
    d = d.sort_values("pp", ascending=False)
    d["mr"] = np.arange(1, len(d) + 1)
    d = d.sort_values("sadp")
    d["ar"] = np.arange(1, len(d) + 1)
    d["br"] = W * d["mr"] + (1 - W) * d["ar"]
    for (k, ps), tgt in OVER.items():
        if ps != p:
            continue
        m = d["k"] == k
        if m.any():
            d.loc[m, "br"] = float(tgt) - 0.5
            print("  OVERRIDE %s -> %s%d" % (k, p, tgt))
    curve = np.sort(d["pp"].values)[::-1]
    d = d.sort_values(["br", "mr"])
    for i, (_, r) in enumerate(d.iterrows()):
        NEW[(r["k"], p)] = float(curve[i])

B["np_"] = [NEW.get((k, p), np.nan)
            for k, p in zip(B["k"], B["position"])]
hit = B["np_"].notna()
B["mv"] = B["np_"] - B["pp"]
print("\nreslotted %d players" % int(hit.sum()))
print("mean absolute move: %.2f ppg"
      % B.loc[hit, "mv"].abs().mean())

print("\n=== BIGGEST DROPS ===")
for _, r in B.nsmallest(10, "mv").iterrows():
    print("  %-22s %-3s %6.2f -> %6.2f  %+6.2f"
          " (adp %.0f)"
          % (str(r["player_display_name"])[:22],
             r["position"], r["pp"], r["np_"],
             r["mv"], r["sadp"]))
print("\n=== BIGGEST RISES ===")
for _, r in B.nlargest(10, "mv").iterrows():
    print("  %-22s %-3s %6.2f -> %6.2f  %+6.2f"
          " (adp %.0f)"
          % (str(r["player_display_name"])[:22],
             r["position"], r["pp"], r["np_"],
             r["mv"], r["sadp"]))

B.loc[hit, "points"] = B.loc[hit, "np_"].round(2)
B.drop(columns=["k", "pp", "np_", "mv", "sadp"]).to_csv(
    "board_final.csv", index=False)
print("\nwrote board_final.csv")
print("NEXT: python3 221_vorp_rank.py")
