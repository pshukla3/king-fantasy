import pandas as pd

I = pd.read_csv("injuries_2026.csv")
print("before: %d rows" % len(I))

# player, team, pos, status, injury, weeks_out, kind, note
NEW = [
 ("Ja'Marr Chase","CIN","WR","QUESTIONABLE","Knee","","camp",
  "CBS 8/25: knee, questionable Wk1 vs TB"),
 ("Trey Benson","ARI","RB","IR","Knee","","camp",
  "CBS 8/25: placed on IR"),
 ("James Conner","ARI","RB","QUESTIONABLE","Foot","","camp",
  "CBS 8/23: foot"),
 ("Xavier Weaver","ARI","WR","IR","Hamstring","","camp",""),
 ("Elijah Higgins","ARI","TE","QUESTIONABLE","Concussion","","camp",""),
 ("Carson Beck","ARI","QB","QUESTIONABLE","Ribs","","camp",""),
 ("Trey Sermon","ATL","RB","IR","Undisclosed","","camp",""),
 ("Ty Johnson","BUF","RB","QUESTIONABLE","Lower Leg","","camp",""),
 ("Keon Coleman","BUF","WR","QUESTIONABLE","Foot","","camp",""),
 ("Khalil Shakir","BUF","WR","QUESTIONABLE","Undisclosed","","camp",""),
 ("Xavier Legette","CAR","WR","QUESTIONABLE","Ankle","","camp",""),
 ("Haynes King","CAR","QB","QUESTIONABLE","Hamstring","","camp",""),
 ("Nikola Kalinic","CHI","TE","IR","Knee","","camp",""),
 ("Cedric Tillman","CLE","WR","QUESTIONABLE","Undisclosed","","camp",""),
 ("Jamari Thrash","CLE","WR","IR","Undisclosed","","camp",""),
 ("Jack Stoll","CLE","TE","IR","Undisclosed","","camp",""),
 ("DJ Rogers","DAL","TE","QUESTIONABLE","Knee","","camp",""),
 ("Michael Trigg","DAL","TE","QUESTIONABLE","Toe","","camp",""),
 ("Princeton Fant","DAL","TE","IR","Knee","","camp","ACL + MCL"),
 ("Caleb Lohner","DEN","TE","QUESTIONABLE","Undisclosed","","camp",""),
 ("Cedrick Wilson Jr.","DET","WR","IR","Knee","","camp",""),
 ("Isiah Pacheco","DET","RB","QUESTIONABLE","Knee","","camp",
  "CBS 8/10: MCL"),
 ("Sione Vaki","DET","RB","QUESTIONABLE","Back","","camp",""),
 ("Jabari Small","DET","RB","QUESTIONABLE","Concussion","","camp",""),
 ("Josh Jacobs","GB","RB","QUESTIONABLE","Groin","","camp",
  "CBS 8/23: groin"),
 ("J. Michael Sturdivant","GB","WR","QUESTIONABLE","Concussion","",
  "camp",""),
 ("Noah Whittington","HOU","RB","QUESTIONABLE","Ankle","","camp",""),
 ("Jawhar Jordan","HOU","RB","QUESTIONABLE","Hip","","camp",""),
 ("Brevin Jordan","HOU","TE","QUESTIONABLE","Knee","","camp",""),
 ("Josh Downs","IND","WR","QUESTIONABLE","Undisclosed","","camp",
  "CBS 8/25"),
 ("Brian Thomas Jr.","JAX","WR","QUESTIONABLE","Shoulder","","camp",
  "CBS 8/25: shoulder"),
 ("Kenneth Walker III","KC","RB","QUESTIONABLE","Foot","","camp",
  "CBS 8/25: foot"),
 ("Jeff Caldwell","KC","WR","IR","Knee","","camp",""),
 ("Keaton Mitchell","LAC","RB","QUESTIONABLE","Undisclosed","","camp",
  "CBS 8/25"),
 ("Terrance Ferguson","LA","TE","QUESTIONABLE","Undisclosed","","camp",
  "general soreness"),
 ("TreVeyon Henderson","NE","RB","QUESTIONABLE","Ankle","","camp",
  "CBS 8/25: ankle"),
 ("Lan Larison","NE","RB","QUESTIONABLE","Undisclosed","","camp",""),
 ("Chris Olave","NO","WR","QUESTIONABLE","Undisclosed","","camp",
  "CBS 8/25: upper body"),
 ("Ty Chandler","NO","RB","IR","Knee","","camp",""),
 ("Moliki Matavao","NO","TE","IR","Knee","","camp",""),
 ("Oscar Delp","NO","TE","QUESTIONABLE","Hamstring","","camp",""),
 ("Calvin Austin III","NYG","WR","QUESTIONABLE","Knee","","camp",""),
 ("Theo Johnson","NYG","TE","QUESTIONABLE","Undisclosed","","camp",""),
 ("Caullin Lacy","NYJ","WR","IR","Undisclosed","","camp",""),
 ("Ja'Quinden Jackson","PHI","RB","IR","Undisclosed","","camp",""),
 ("Eli Stowers","PHI","TE","QUESTIONABLE","Hamstring","","camp",""),
 ("Emanuel Wilson","SEA","RB","QUESTIONABLE","Hamstring","","camp",""),
 ("Tory Horton","SEA","WR","QUESTIONABLE","Undisclosed","","camp",""),
 ("Jacob Cowing","SF","WR","QUESTIONABLE","Groin","","camp",""),
 ("Kurtis Rourke","SF","QB","QUESTIONABLE","Ribs","","camp",""),
 ("Kalel Mullings","TEN","RB","QUESTIONABLE","Hip","","camp",""),
 ("Mitchell Trubisky","TEN","QB","QUESTIONABLE","Undisclosed","","camp",
  "biceps"),
 ("Rachaad White","WAS","RB","QUESTIONABLE","Hamstring","","camp",
  "CBS 8/25: hamstring"),
 ("Jacory Croskey-Merritt","WAS","RB","QUESTIONABLE","Undisclosed","",
  "camp","CBS 8/25: lower body"),
 ("Ben Sinnott","WAS","TE","QUESTIONABLE","Undisclosed","","camp",
  "oblique"),
]

# status / injury changes to rows we already had
CHG = [
 ("Mike Evans","QUESTIONABLE","Groin","CBS 8/25: groin, was quad"),
 ("Kyle Monangai","QUESTIONABLE","Knee","CBS 8/17: upgraded from Out"),
 ("Tip Reiman","PUP","Ankle","CBS 8/21: ankle named"),
 ("Luke Musgrave","PUP","Neck","CBS 8/23: neck named"),
 ("Tyrell Shavers","PUP","Knee","CBS 8/22: ACL, expected back Wk1"),
 ("Tucker Kraft","QUESTIONABLE","Knee","CBS 8/23: ACL, Q for Wk1"),
]

COLS = list(I.columns)
key = I["player"].astype(str)

for nm, st, inj, note in CHG:
    m = key == nm
    if not m.any():
        print("  CHG not found: %s" % nm)
        continue
    o = I.loc[m, "status"].iloc[0]
    oi = I.loc[m, "injury"].iloc[0]
    I.loc[m, "status"] = st
    I.loc[m, "injury"] = inj
    I.loc[m, "note"] = note
    print("  CHG %-22s %-12s %-11s -> %-12s %s"
          % (nm, o, oi, st, inj))

have = set(I["player"].astype(str))
add = [r for r in NEW if r[0] not in have]
skip = [r[0] for r in NEW if r[0] in have]
if skip:
    print("\n  already on file, left alone: %s" % ", ".join(skip))

if add:
    A = pd.DataFrame(add, columns=COLS)
    I = pd.concat([I, A], ignore_index=True)
    print("\n  ADDED %d rows:" % len(add))
    for r in add:
        print("    %-24s %-4s %-3s %-12s %s"
              % (r[0], r[1], r[2], r[3], r[4]))

I = I.drop_duplicates("player", keep="last")
I.to_csv("injuries_2026.csv", index=False)
print("\nafter: %d rows" % len(I))
print("skill rows: %d"
      % int(I["pos"].isin(["QB", "RB", "WR", "TE", "K"]).sum()))
