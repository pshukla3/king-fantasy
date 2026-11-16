import json
import pandas as pd

S = pd.read_csv("sleeper_cmp.csv")
B = pd.read_csv("board_final.csv", low_memory=False)
C = json.load(open("player_cards.json"))
import re

def key(n):
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "",
               str(n).lower())
    return re.sub(r"[^a-z]", "", n)

B["k"] = B["player_display_name"].apply(key)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B["eg"] = pd.to_numeric(B["exp_games"], errors="coerce")
B = B[B["pp"].notna()]
M = B.merge(S[["k", "gp", "ours_pts", "tar", "rec",
               "cyd", "ctd", "adp"]].rename(
                   columns={"adp": "sadp"}),
            on="k", how="inner")
M["our17"] = M["pp"] * 17.0
M["slp18"] = M["ours_pts"]
M["slp17"] = M["ours_pts"] * 17.0 / M["gp"].clip(lower=1)
M["shown"] = M["pp"] * (M["eg"] / 17.0).clip(upper=1.0) * 17

CARD = {v["nm"]: v for v in C.values()}

print("=== WR: OURS vs SLEEPER, SEASON POINTS ===")
print("  shown = what the site displays today\n")
print("  %-22s %6s %6s %6s %6s %7s"
      % ("player", "shown", "our17", "slp17", "slp18",
         "vs s17"))
print("  " + "-" * 62)
W = M[M["position"] == "WR"].nlargest(24, "pp")
for _, r in W.iterrows():
    print("  %-22s %6.0f %6.0f %6.0f %6.0f %+6.1f%%"
          % (str(r["player_display_name"])[:22],
             r["shown"], r["our17"], r["slp17"],
             r["slp18"],
             100.0 * (r["our17"] / r["slp17"] - 1)))

print("\n=== COMPONENT CHECK, NAMED RECEIVERS ===")
print("  %-20s %-8s %5s %5s %6s %5s"
      % ("player", "src", "tar", "rec", "yds", "td"))
for nm in ["Jaxon Smith-Njigba", "A.J. Brown",
           "Jaylen Waddle", "Ladd McConkey",
           "DeVonta Smith", "Puka Nacua"]:
    h = M[M["player_display_name"] == nm]
    if not len(h):
        print("  %-20s NOT MATCHED" % nm[:20])
        continue
    r = h.iloc[0]
    c = CARD.get(nm, {})
    p = c.get("p26")
    if p:
        print("  %-20s %-8s %5.0f %5.0f %6.0f %5.1f"
              % (nm[:20], "ours", p["tar"], p["rec"],
                 p["cyd"], p["ctd"]))
    print("  %-20s %-8s %5.0f %5.0f %6.0f %5.1f"
          % ("", "sleeper", r["tar"], r["rec"],
             r["cyd"], r["ctd"]))

print("\n=== QB: WHERE ARE WE +23%% HIGH? ===")
Q = M[M["position"] == "QB"].nlargest(16, "pp")
print("  %-20s %6s %6s %7s"
      % ("player", "our17", "slp17", "gap"))
for _, r in Q.iterrows():
    print("  %-20s %6.0f %6.0f %+6.1f%%"
          % (str(r["player_display_name"])[:20],
             r["our17"], r["slp17"],
             100.0 * (r["our17"] / r["slp17"] - 1)))
