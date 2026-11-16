import numpy as np, pandas as pd, json
import nflreadpy as nfl

# How much does a passing offence drop when the usual
# starter is replaced? Measure it rather than pick it.
d = nfl.load_player_stats(seasons=[2023, 2024, 2025, 2026]
                          ).to_pandas()
tc = "team" if "team" in d.columns else "recent_team"
q = d[(d["position"] == "QB") & (d.get("attempts", 0) >= 5)].copy()
q["att"] = q["attempts"]
q["pyd"] = q["passing_yards"]
q["ptd"] = q["passing_tds"]

rows = []
for (tm, sn), g in q.groupby([tc, "season"]):
    tot = g.groupby("player_id")["att"].sum()
    if len(tot) < 2:
        continue
    star = tot.idxmax()
    for _, r in g.iterrows():
        rows.append({"tm": tm, "season": sn,
                     "week": r["week"],
                     "is_qb1": r["player_id"] == star,
                     "att": r["att"], "pyd": r["pyd"],
                     "ptd": r["ptd"]})
R = pd.DataFrame(rows)
a = R[R["is_qb1"]]
b = R[~R["is_qb1"]]
print("QB1 starts: %d   backup starts: %d" % (len(a), len(b)))
print()
print("  %-16s %10s %10s %8s"
      % ("", "QB1", "BACKUP", "RATIO"))
for lbl, col in (("attempts/gm", "att"),
                 ("pass yards/gm", "pyd"),
                 ("pass TD/gm", "ptd")):
    x, y = a[col].mean(), b[col].mean()
    print("  %-16s %10.2f %10.2f %8.3f"
          % (lbl, x, y, y / x if x else 0))
ya = a["pyd"].sum() / max(a["att"].sum(), 1)
yb = b["pyd"].sum() / max(b["att"].sum(), 1)
ta = a["ptd"].sum() / max(a["att"].sum(), 1)
tb2 = b["ptd"].sum() / max(b["att"].sum(), 1)
print("  %-16s %10.2f %10.2f %8.3f"
      % ("yards/attempt", ya, yb, yb / ya))
print("  %-16s %10.4f %10.4f %8.3f"
      % ("TD/attempt", ta, tb2, tb2 / ta))

OUT = {"att_mult": float(b["att"].mean() / a["att"].mean()),
       "ypa_mult": float(yb / ya),
       "tdr_mult": float(tb2 / ta)}
json.dump(OUT, open("qbinj.json", "w"), indent=1)
print("\nwrote qbinj.json: %s"
      % {k: round(v, 3) for k, v in OUT.items()})

print("\n=== who is hurt right now ===")
INJ = json.load(open("site/_inj.json"))
hurt = [(v.get("n"), v.get("tm"), v.get("status"),
         v.get("type"))
        for v in INJ.values()
        if v.get("status") and "Active" not in str(v.get("status"))]
WATCH = ("Caleb Williams", "Jaxson Dart", "Jayden Daniels",
         "Sam Darnold")
for n_, t_, s_, ty in hurt:
    if n_ in WATCH:
        print("  %-20s %-4s %-22s %s" % (n_, t_, s_, ty))
print("  (total players with a designation: %d)" % len(hurt))
