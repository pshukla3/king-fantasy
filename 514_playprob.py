import json
import nflreadpy as nfl

YR = [2023, 2024, 2025]
inj = nfl.load_injuries(YR).to_pandas()
inj = inj[inj["position"].isin(["QB", "RB", "WR", "TE"])]
sn = nfl.load_snap_counts(YR).to_pandas()
sn["offense_snaps"] = sn["offense_snaps"].fillna(0)
sn = sn[sn["offense_snaps"] > 0][
    ["season", "week", "player", "team"]].copy()
sn["active"] = 1
m = inj.merge(sn,
              left_on=["season", "week", "full_name", "team"],
              right_on=["season", "week", "player", "team"],
              how="left")
m["active"] = m["active"].fillna(0)

PS = (("Full Participation in Practice", "Full"),
      ("Limited Participation in Practice", "Limited"),
      ("Did Not Participate In Practice", "DNP"))
OUT = {}
print("=== WAS HE ON THE FIELD? (snap counts) ===")
for rs in ("Out", "Doubtful", "Questionable"):
    s = m[m["report_status"] == rs]
    if len(s) < 25:
        continue
    OUT[rs] = {"any": round(float(s["active"].mean()), 4)}
    print("  %-26s %5.1f%%  (n=%d)"
          % (rs, s["active"].mean() * 100, len(s)))
    for full, short in PS:
        q = s[s["practice_status"] == full]
        if len(q) >= 25:
            OUT[rs][short] = round(float(q["active"].mean()), 4)
            print("      + %-8s %5.1f%%  (n=%d)"
                  % (short, q["active"].mean() * 100, len(q)))
    print()
json.dump(OUT, open("playprob.json", "w"), indent=1)
print("wrote playprob.json")
