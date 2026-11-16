import json
import re
import pandas as pd

J = json.load(open("sleeper_proj_raw.json"))
SC = pd.read_csv("league_scoring.csv")
V = dict(zip(SC["key"], SC["value"]))

def sv(k):
    return float(V.get(k, 0.0))

def key(n):
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "",
               str(n).lower())
    return re.sub(r"[^a-z]", "", n)

rows = []
for d in J:
    s = d.get("stats") or {}
    p = d.get("player") or {}
    nm = ((p.get("first_name") or "") + " "
          + (p.get("last_name") or "")).strip()
    def g(k):
        v = s.get(k)
        return 0.0 if v is None else float(v)
    ours = (g("pass_yd") * sv("pass_yd")
            + g("pass_td") * sv("pass_td")
            + g("pass_int") * sv("pass_int")
            + g("rush_yd") * sv("rush_yd")
            + g("rush_td") * sv("rush_td")
            + g("rec") * sv("rec")
            + g("rec_yd") * sv("rec_yd")
            + g("rec_td") * sv("rec_td")
            + g("fum_lost") * sv("fum_lost"))
    rows.append({"k": key(nm), "nm": nm,
                 "pos": p.get("position"),
                 "tm": d.get("team"),
                 "gp": g("gp"),
                 "slp_pts": g("pts_ppr"),
                 "ours_pts": ours,
                 "tar": g("rec_tgt"), "rec": g("rec"),
                 "cyd": g("rec_yd"), "ctd": g("rec_td"),
                 "adp": s.get("adp_ppr")})
S = pd.DataFrame(rows)
S = S[S["pos"].isin(["QB", "RB", "WR", "TE"])]
S = S.sort_values("ours_pts", ascending=False)
S = S.drop_duplicates("k")
S.to_csv("sleeper_cmp.csv", index=False)

print("=== SLEEPER GAMES ASSUMPTION ===")
print(S["gp"].value_counts().head(5).to_string())

print("\n=== SCORING SYSTEM GAP ===")
q = S[(S["pos"] == "QB") & (S["slp_pts"] > 200)]
print("  QBs: sleeper pts_ppr avg %.1f | "
      "same stats, your scoring %.1f  (%+.1f)"
      % (q["slp_pts"].mean(), q["ours_pts"].mean(),
         q["ours_pts"].mean() - q["slp_pts"].mean()))

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B = B[B["pp"].notna()]
M = B.merge(S, on="k", how="inner",
            suffixes=("", "_s"))
print("\nboard %d | sleeper %d | matched %d"
      % (len(B), len(S), len(M)))

M["our17"] = M["pp"] * 17.0
M["slp17"] = M["ours_pts"] * (17.0 / M["gp"].clip(lower=1))
M["gap"] = 100.0 * (M["our17"] / M["slp17"] - 1)

print("\n=== GAP BY POSITION (both at 17 games,"
      " both your scoring) ===")
print("  %-4s %5s %9s %9s %8s"
      % ("pos", "n", "ours", "sleeper", "gap"))
for p in ["QB", "RB", "WR", "TE"]:
    d = M[(M["position"] == p) & (M["slp17"] > 80)]
    if len(d) < 10:
        continue
    print("  %-4s %5d %9.1f %9.1f %+7.1f%%"
          % (p, len(d), d["our17"].mean(),
             d["slp17"].mean(), d["gap"].mean()))
