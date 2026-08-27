import pandas as pd

RB1_OPG, RB2_OPG = 17.5, 9.9
SHARE = ((RB1_OPG + RB2_OPG) / 2.0) / RB1_OPG
print("committee factor = %.3f (from script 69 role table)" % SHARE)

C = pd.read_csv("committee_2026.csv")
B = pd.read_csv("board_final.csv", low_memory=False)
NC = "player_display_name"

if "base_points" not in B.columns:
    B["base_points"] = B["points"]
else:
    B["points"] = B["base_points"]

B["committee"] = 0
hit, miss = [], []
for _, r in C.iterrows():
    nm = str(r["player"]).strip()
    m = B[NC].astype(str).str.strip() == nm
    if not m.any():
        miss.append(nm)
        continue
    old = float(B.loc[m, "points"].iloc[0])
    B.loc[m, "points"] = old * SHARE
    B.loc[m, "committee"] = 1
    hit.append((nm, str(r["team"]), old, old * SHARE))

print("\n=== COMMITTEE DISCOUNT APPLIED ===")
for nm, tm, o, n in hit:
    print("  %-22s %-4s %5.2f -> %5.2f  (%+.2f)"
          % (nm, tm, o, n, n - o))
if miss:
    print("\nNOT ON BOARD: %s" % ", ".join(miss))

B.to_csv("board_committee.csv", index=False)
print("\nSaved board_committee.csv (%d discounted)" % len(hit))
