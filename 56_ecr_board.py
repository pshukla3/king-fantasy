import pandas as pd, io

RAW = """1,Jahmyr Gibbs,RB,DET
2,Ja'Marr Chase,WR,CIN
3,Bijan Robinson,RB,ATL
4,Puka Nacua,WR,LAR
5,Jaxon Smith-Njigba,WR,SEA
6,Amon-Ra St. Brown,WR,DET
7,Jonathan Taylor,RB,IND
8,CeeDee Lamb,WR,DAL
9,James Cook III,RB,BUF
10,Christian McCaffrey,RB,SF
11,Justin Jefferson,WR,MIN
12,A.J. Brown,WR,NE
13,Nico Collins,WR,HOU
14,Derrick Henry,RB,BAL
15,Drake London,WR,ATL
16,Brock Bowers,TE,LV
17,Saquon Barkley,RB,PHI
18,Ashton Jeanty,RB,LV
19,George Pickens,WR,DAL
20,Chase Brown,RB,CIN
21,Trey McBride,TE,ARI
22,Josh Allen,QB,BUF
23,Kenneth Walker III,RB,KC
24,Omarion Hampton,RB,LAC
25,Chris Olave,WR,NO
26,De'Von Achane,RB,MIA
27,Malik Nabers,WR,NYG
28,Rashee Rice,WR,KC
29,Lamar Jackson,QB,BAL
30,Zay Flowers,WR,BAL
31,Kyren Williams,RB,LAR
32,Tee Higgins,WR,CIN
33,DeVonta Smith,WR,PHI
34,Drake Maye,QB,NE
35,Javonte Williams,RB,DAL
36,Josh Jacobs,RB,GB
37,Tetairoa McMillan,WR,CAR
38,Emeka Egbuka,WR,TB
39,Colston Loveland,TE,CHI
40,Breece Hall,RB,NYJ
41,Ladd McConkey,WR,LAC
42,Jaylen Waddle,WR,DEN
43,Joe Burrow,QB,CIN
44,Jeremiyah Love,RB,ARI
45,Jameson Williams,WR,DET
46,Davante Adams,WR,LAR
47,Terry McLaurin,WR,WAS
48,Travis Etienne Jr.,RB,NO
49,Garrett Wilson,WR,NYJ
50,Jayden Daniels,QB,WAS
51,D'Andre Swift,RB,CHI
52,Christian Watson,WR,GB
53,Quinshon Judkins,RB,CLE
54,Rome Odunze,WR,CHI
55,Cam Skattebo,RB,NYG
56,David Montgomery,RB,HOU
57,Jalen Hurts,QB,PHI
58,Bucky Irving,RB,TB
59,Luther Burden III,WR,CHI
60,Mike Evans,WR,SF
61,DJ Moore,WR,BUF
62,Tucker Kraft,TE,GB
63,Tyler Warren,TE,IND
64,Bhayshul Tuten,RB,JAC
65,TreVeyon Henderson,RB,NE
66,Jadarian Price,RB,SEA
67,Caleb Williams,QB,CHI
68,Justin Herbert,QB,LAC
69,Parker Washington,WR,JAC
70,Marvin Harrison Jr.,WR,ARI
71,Brian Thomas Jr.,WR,JAC
72,Trevor Lawrence,QB,JAC
73,Jaylen Warren,RB,PIT
74,Tony Pollard,RB,TEN
75,Dak Prescott,QB,DAL
76,Carnell Tate,WR,TEN
77,Rhamondre Stevenson,RB,NE
78,DK Metcalf,WR,PIT
79,Sam LaPorta,TE,DET
80,Rico Dowdle,RB,PIT
81,Courtland Sutton,WR,DEN
82,J.K. Dobbins,RB,DEN
83,Blake Corum,RB,LAR
84,Harold Fannin Jr.,TE,CLE
85,Alec Pierce,WR,IND
86,Quentin Johnston,WR,LAC
87,Kyle Pitts Sr.,TE,ATL
88,Jonathon Brooks,RB,CAR
89,Chris Godwin Jr.,WR,TB
90,George Kittle,TE,SF
91,Jacory Croskey-Merritt,RB,WAS
92,Brock Purdy,QB,SF
93,Jaxson Dart,QB,NYG
94,Chuba Hubbard,RB,CAR
95,Jordan Mason,RB,MIN
96,Kyle Monangai,RB,CHI
97,Jordan Addison,WR,MIN
98,Patrick Mahomes II,QB,KC
99,Bo Nix,QB,DEN
100,Michael Wilson,WR,ARI
101,Dalton Kincaid,TE,BUF
102,Matthew Stafford,QB,LAR
103,Jayden Reed,WR,GB
104,Jared Goff,QB,DET
105,Michael Pittman Jr.,WR,PIT
106,RJ Harvey,RB,DEN
107,Makai Lemon,WR,PHI
108,Travis Kelce,TE,KC
109,Rachaad White,RB,WAS
110,Kyler Murray,QB,MIN
111,Dallas Goedert,TE,PHI
112,Isaiah Likely,TE,NYG
113,Mark Andrews,TE,BAL
114,Jakobi Meyers,WR,JAC
115,Kenny Gainwell,RB,TB
116,Josh Downs,WR,IND
117,Chris Rodriguez Jr.,RB,JAC
118,Aaron Jones Sr.,RB,MIN
119,Baker Mayfield,QB,TB
120,Xavier Worthy,WR,KC
121,Jordan Love,QB,GB
122,Wan'Dale Robinson,WR,TEN
123,Stefon Diggs,WR,WAS
124,Tyler Shough,QB,NO
125,Matthew Golden,WR,GB
126,Tyler Allgeier,RB,ARI
127,Jake Ferguson,TE,DAL
128,KC Concepcion,WR,CLE
129,Jordyn Tyson,WR,NO
130,Romeo Doubs,WR,NE
131,Woody Marks,RB,HOU
132,Jalen Coker,WR,CAR
133,Malik Willis,QB,MIA
134,Zach Charbonnet,RB,SEA
135,Tyrone Tracy Jr.,RB,NYG
136,Juwan Johnson,TE,NO
137,Khalil Shakir,WR,BUF
138,Tank Bigsby,RB,PHI
139,Rashid Shaheed,WR,SEA
140,Sam Darnold,QB,SEA
141,De'Zhaun Stribling,WR,SF
142,Deebo Samuel Sr.,WR,SF
143,C.J. Stroud,QB,HOU
144,Keaton Mitchell,RB,LAC
145,Isiah Pacheco,RB,DET
146,Hunter Henry,TE,NE
147,Jonah Coleman,RB,DEN
148,Brian Robinson Jr.,RB,ATL
149,Brenton Strange,TE,JAC
150,Tyjae Spears,RB,TEN
151,Daniel Jones,QB,IND
152,Denzel Boston,WR,CLE
153,Alvin Kamara,RB,NO
154,Cam Ward,QB,TEN
155,Houston Texans,DST,HOU
156,Braelon Allen,RB,NYJ
157,Dylan Sampson,RB,CLE
158,Chig Okonkwo,TE,WAS
159,Jauan Jennings,WR,MIN
160,Adonai Mitchell,WR,NYJ
161,Jalen McMillan,WR,TB
162,Denver Broncos,DST,DEN
163,Oronde Gadsden II,TE,LAC
164,Jerry Jeudy,WR,CLE
165,Tre Tucker,WR,LV
166,Seattle Seahawks,DST,SEA
167,Los Angeles Rams,DST,LAR
168,Bryce Young,QB,CAR
169,MarShawn Lloyd,RB,GB
170,Philadelphia Eagles,DST,PHI
171,Tre' Harris,WR,LAC
172,Dalton Schultz,TE,HOU
173,Jalen Nailor,WR,LV
174,Mike Washington Jr.,RB,LV
175,Emmett Johnson,RB,KC
176,AJ Barner,TE,SEA
177,Omar Cooper Jr.,WR,NYJ
178,Terrance Ferguson,TE,LAR
179,Brandon Aubrey,K,DAL
180,Sean Tucker,RB,TB
181,Travis Hunter,WR,JAC
182,Ray Davis,RB,BUF
183,New England Patriots,DST,NE
184,Pittsburgh Steelers,DST,PIT
185,Nicholas Singleton,RB,TEN
186,Minnesota Vikings,DST,MIN
187,Kayshon Boutte,WR,NE
188,Kimani Vidal,RB,LAC
189,Dontayvion Wicks,WR,PHI
190,Jacksonville Jaguars,DST,JAC
191,Ryan Flournoy,WR,DAL
192,Calvin Ridley,WR,TEN
193,Cameron Dicker,K,LAC
194,Los Angeles Chargers,DST,LAC
195,Ka'imi Fairbairn,K,HOU
196,Cam Little,K,JAC
197,Baltimore Ravens,DST,BAL
198,Jacoby Brissett,QB,ARI
199,Emanuel Wilson,RB,SEA
200,Kenyon Sadiq,TE,NYJ"""

b = pd.read_csv(io.StringIO(RAW), names=["ecr", "player", "position", "team"])
b["pos_rank"] = b.groupby("position")["ecr"].rank(method="min").astype(int)
b.to_csv("board_ecr.csv", index=False)
print("board size:", len(b), "|", b["position"].value_counts().to_dict())

TEAMS, ROUNDS = 10, 15
STARTERS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "DST", "K"]
CAP = {"QB": 1, "TE": 2, "DST": 1, "K": 1, "RB": 6, "WR": 7}
LATE = {"DST": 11, "K": 12}
MIN = {"RB": 2, "WR": 2, "TE": 1}

pool = b.to_dict("records")
rosters = {t: [] for t in range(1, TEAMS + 1)}
picks = []

for rd in range(1, ROUNDS + 1):
    order = range(1, TEAMS + 1) if rd % 2 else range(TEAMS, 0, -1)
    for slot, tm in enumerate(order, 1):
        cnt = {}
        for p in rosters[tm]:
            cnt[p["position"]] = cnt.get(p["position"], 0) + 1
        left = ROUNDS - rd + 1
        need = [q for q in ("DST", "K") if cnt.get(q, 0) == 0]
        need += [q for q, m in MIN.items() if cnt.get(q, 0) < m]
        forced = need if len(need) >= left else None

        best = None
        for p in pool:
            pos = p["position"]
            if cnt.get(pos, 0) >= CAP.get(pos, 99):
                continue
            if pos in LATE and rd < LATE[pos]:
                continue
            if forced and pos not in forced:
                continue
            best = p
            break
        if best is None:
            best = next(p for p in pool
                        if cnt.get(p["position"], 0) < CAP.get(p["position"], 99))
        pool.remove(best)
        rosters[tm].append(best)
        picks.append((rd, slot, tm, best))

print("\n=== ECR SNAKE DRAFT — 10tm | QB/RB/RB/WR/WR/TE/FLEX/FLEX/DST/K + 5 bench ===")
for rd in range(1, ROUNDS + 1):
    print(f"\n--- Round {rd} ---")
    for r, s, tm, p in picks:
        if r == rd:
            print(f"  {r}.{s:02d}  Team{tm:<3d} {p['player']:<24s} "
                  f"{p['position']}{p['pos_rank']:<4d} {p['team']:<4s} ECR {p['ecr']}")

print("\n\n=== TEAMS ===")
bad = 0
for tm in range(1, TEAMS + 1):
    r = sorted(rosters[tm], key=lambda x: x["ecr"])
    n = {}
    for p in r:
        n[p["position"]] = n.get(p["position"], 0) + 1
    ok = n.get("QB", 0) == 1 and n.get("DST", 0) == 1 and n.get("K", 0) == 1
    bad += 0 if ok else 1
    avg = sum(p["ecr"] for p in r) / len(r)
    print(f"\n--- Team {tm}   avg ECR {avg:.1f}   "
          f"({n.get('QB',0)}QB {n.get('RB',0)}RB {n.get('WR',0)}WR {n.get('TE',0)}TE "
          f"{n.get('DST',0)}DST {n.get('K',0)}K){'' if ok else '  <-- INVALID'}")
    for p in r:
        print(f"  {p['position']:<4s} {p['player']:<24s} {p['team']:<4s} ECR {p['ecr']}")
print(f"\nrosters violating 1QB/1DST/1K: {bad}")
