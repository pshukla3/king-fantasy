import re
import pandas as pd

SUF = re.compile(r"\b(jr|sr|ii|iii|iv)\b")

def key(s):
    s = re.sub(r"[^a-z ]", " ", str(s).lower())
    return re.sub(r"\s+", "", SUF.sub(" ", s))

# name, team, status, games_mult, points_mult, note
SEED = [
    ("Zach Charbonnet", "SEA", "PUP", 0.76, 1.00,
     "torn ACL in playoffs; Reserve/PUP = 4 games min"),
    ("Ricky Pearsall", "SF", "IR", 0.00, 1.00,
     "on injured reserve"),
    ("Jayden Higgins", "HOU", "IR", 0.00, 1.00,
     "on injured reserve"),
    ("Luke Musgrave", "GB", "PUP", 0.76, 1.00,
     "placed on PUP"),
    ("Ashton Jeanty", "LV", "QUESTIONABLE", 0.94, 1.00,
     "ankle sprain in practice, small risk for wk1"),
    ("Luther Burden III", "CHI", "QUESTIONABLE", 0.88, 1.00,
     "wk1 return not assured, team cautious"),
    ("Chuba Hubbard", "CAR", "QUESTIONABLE", 0.94, 1.00,
     "hamstring, week-to-week, HC expects wk1"),
    ("Tyler Warren", "IND", "QUESTIONABLE", 0.94, 1.00,
     "adductor strain, wk1 not in jeopardy"),
    ("TreVeyon Henderson", "NE", "", 1.00, 1.00,
     "ankle in practice, now expected wk1"),
    ("Tucker Kraft", "GB", "", 1.00, 1.00,
     "full 11-on-11, expected full go wk1"),
    ("Alec Pierce", "IND", "", 1.00, 1.00,
     "activated off PUP Aug 27"),
    ("George Kittle", "SF", "", 1.00, 1.00,
     "activated off PUP, ahead of schedule"),
    ("Malik Nabers", "NYG", "", 1.00, 1.00,
     "on track for wk1"),
]

N = pd.DataFrame(SEED, columns=["nm", "tm", "status",
                                "gm", "pm", "note"])
N["k"] = N["nm"].apply(key)
N.to_csv("injury_news_2026.csv", index=False)

B = pd.read_csv("board_final.csv", low_memory=False)
B["k"] = B["player_display_name"].apply(key)
LK = {r["k"]: r for _, r in N.iterrows()}

print("=== APPLYING %d NEWS ITEMS ===" % len(N))
print("  %-22s %-4s %-14s %5s %7s"
      % ("player", "tm", "status", "gmult", "ppg"))
print("  " + "-" * 58)
hit = 0
for i in B.index:
    r = LK.get(B.at[i, "k"])
    if r is None:
        continue
    hit += 1
    B.at[i, "status"] = r["status"] if r["status"] else None
    if "games_mult" in B.columns:
        B.at[i, "games_mult"] = float(r["gm"])
    pp = pd.to_numeric(pd.Series([B.at[i, "points"]]),
                       errors="coerce").iloc[0]
    print("  %-22s %-4s %-14s %5.2f %7s"
          % (str(B.at[i, "player_display_name"])[:22],
             str(B.at[i, "team"])[:4],
             r["status"] or "healthy", r["gm"],
             "--" if pp != pp else "%.2f" % pp))

miss = [r["nm"] for _, r in N.iterrows()
        if r["k"] not in set(B["k"])]
print("\n  matched %d of %d" % (hit, len(N)))
if miss:
    print("  NOT ON BOARD: %s" % miss)
B.drop(columns=["k"]).to_csv("board_final.csv", index=False)

print("\n" + "=" * 58)
print("=== IMPACT ON THE NEW MODEL'S TOP GUYS ===")
try:
    P = pd.read_csv("proj_2026.csv")
    P["k"] = P["player_display_name"].apply(key)
    P = P.merge(N[["k", "status", "gm", "note"]],
                on="k", how="inner")
    if len(P):
        print("  %-22s %-4s %6s %6s %6s  %s"
              % ("player", "pos", "PROJ", "gmult",
                 "adj17", "note"))
        print("  " + "-" * 76)
        for _, r in P.sort_values(
                "proj", ascending=False).iterrows():
            print("  %-22s %-4s %6.2f %6.2f %6.0f  %s"
                  % (str(r["player_display_name"])[:22],
                     r["position"], r["proj"], r["gm"],
                     r["proj"] * 17 * r["gm"],
                     str(r["note"])[:34]))
    else:
        print("  none of the flagged players are in"
              " proj_2026.csv")
except IOError:
    print("  proj_2026.csv not found")

print("\n=== CUTDOWN WARNING ===")
print("  53-man deadline is Sun Aug 30 2026.")
print("  ~1,184 players get released league-wide.")
print("  Re-run 215 + 216 + 217 on Mon Aug 31 or the")
print("  board will carry cut players at full value.")
