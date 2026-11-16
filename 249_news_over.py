import os
import pandas as pd

NEWS = [
    ("Josh Jacobs", 0.00,
     "Commissioner's Exempt List - Rotowire, PFT,"
     " Yahoo, CBS, Sporting News (5 outlets)"
     " Aug 30 2026"),
]

B = pd.read_csv("board_final.csv", low_memory=False)
rows = []
if os.path.exists("situation_overrides.csv"):
    rows = pd.read_csv(
        "situation_overrides.csv").to_dict("records")
have = set(str(r["player_id"]) for r in rows)

print("=== NEWS-DRIVEN OVERRIDES ===")
for nm, v, why in NEWS:
    h = B[B["player_display_name"].astype(str) == nm]
    if h.empty:
        print("  %-22s NOT ON BOARD" % nm[:22])
        continue
    r = h.iloc[0]
    pid = str(r["player_id"])
    old = pd.to_numeric(pd.Series([r["points"]]),
                        errors="coerce").iloc[0]
    print("  %-22s %6.2f -> %6.2f"
          % (nm[:22], 0 if old != old else old, v))
    print("     %s" % why)
    if pid in have:
        for x in rows:
            if str(x["player_id"]) == pid:
                x["new_ppg"] = v
                x["reason"] = why
    else:
        rows.append({"player_id": pid,
                     "player_display_name": nm,
                     "new_ppg": v, "reason": why})

pd.DataFrame(rows).to_csv("situation_overrides.csv",
                          index=False)
print("\noverride file now holds %d rows" % len(rows))
