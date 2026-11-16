import pandas as pd

TRUE26 = {
    "A.J. Brown": "NE",
    "Jaylen Waddle": "DEN",
    "Wan'Dale Robinson": "TEN",
    "Romeo Doubs": "NE",
    "Stefon Diggs": "WAS",
    "DeVonta Smith": "PHI",
    "Ladd McConkey": "LAC",
    "Jaxon Smith-Njigba": "SEA",
}
B = pd.read_csv("board_final.csv", low_memory=False)
B["nm"] = B["player_display_name"].astype(str)

print("=== TEAM ASSIGNMENT AUDIT ===")
print("  %-22s %-6s %-6s %s"
      % ("player", "ours", "true", "status"))
print("  " + "-" * 52)
bad = []
for nm, t in sorted(TRUE26.items()):
    h = B[B["nm"] == nm]
    if not len(h):
        print("  %-22s %-6s %-6s NOT ON BOARD"
              % (nm[:22], "--", t))
        continue
    r = h.iloc[0]
    ours = str(r["team"])
    ok = ours == t
    if not ok:
        bad.append((nm, ours, t))
    print("  %-22s %-6s %-6s %s  (%.2f ppg, WR%s)"
          % (nm[:22], ours, t,
             "ok" if ok else "*** STALE ***",
             float(r["points"]) if r["points"] == r["points"]
             else 0.0,
             r["pos_rank"]))

print("\n=== TEAMS AFFECTED BY STALE DATA ===")
if not bad:
    print("  none - all assignments current")
else:
    tms = set()
    for nm, o, t in bad:
        tms.add(o)
        tms.add(t)
    print("  %d stale players touching %d teams: %s"
          % (len(bad), len(tms), sorted(tms)))
    for t in sorted(tms):
        d = B[(B["team"] == t)
              & (B["position"].isin(["WR", "TE", "RB"]))]
        d = d[pd.to_numeric(d["points"],
                            errors="coerce").notna()]
        d = d.sort_values("points", ascending=False)
        print("\n  %s pass-catchers on our board:" % t)
        for _, x in d.head(5).iterrows():
            print("    %-24s %-4s %6.2f ppg"
                  % (str(x["player_display_name"])[:24],
                     x["position"], float(x["points"])))
