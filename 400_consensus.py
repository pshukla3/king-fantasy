import re
import numpy as np
import pandas as pd

W_CONS = 0.60   # consensus is the base, model adjusts

C = """Jahmyr Gibbs|Bijan Robinson|Ja'Marr Chase|Puka Nacua|
Christian McCaffrey|Jaxon Smith-Njigba|Amon-Ra St. Brown|
Jonathan Taylor|Justin Jefferson|James Cook|CeeDee Lamb|
Chase Brown|Ashton Jeanty|Kenneth Walker|Derrick Henry|
Omarion Hampton|Saquon Barkley|De'Von Achane|Malik Nabers|
Chris Olave|Nico Collins|Drake London|Rashee Rice|
Trey McBride|George Pickens|Jeremiyah Love|Zay Flowers|
Breece Hall|Brock Bowers|Javonte Williams|DeVonta Smith|
Kyren Williams|Ladd McConkey|Tee Higgins|D'Andre Swift|
Bucky Irving|Jaylen Waddle|Josh Allen|Garrett Wilson|
Emeka Egbuka|Christian Watson|Colston Loveland|
David Montgomery|Cam Skattebo|Tetairoa McMillan|
Travis Etienne|Mike Evans|DJ Moore|Bhayshul Tuten|
Luther Burden III|Jameson Williams|Jadarian Price|
Lamar Jackson|Quinshon Judkins|Parker Washington|
Davante Adams|Tyler Warren|Rome Odunze|Terry McLaurin|
A.J. Brown|Rhamondre Stevenson|Jaylen Warren|Carnell Tate|
Brian Thomas Jr.|Chuba Hubbard|Caleb Williams|
TreVeyon Henderson|Joe Burrow|Marvin Harrison Jr.|
Jayden Daniels|Chris Godwin Jr.|Tucker Kraft|Jalen Hurts|
Drake Maye|Trevor Lawrence|Stefon Diggs|Matthew Golden|
DK Metcalf|Quentin Johnston|Jacory Croskey-Merritt|
Rico Dowdle|Michael Pittman|J.K. Dobbins|Jordan Mason|
Michael Wilson|Deebo Samuel|RJ Harvey|Jordan Addison|
Sam LaPorta|Tony Pollard|Jalen Coker|Jonathon Brooks|
Alec Pierce|Blake Corum|Justin Herbert|Kyle Monangai|
Dak Prescott|Courtland Sutton|Makai Lemon|Dalton Kincaid|
Josh Downs|Isaiah Likely|George Kittle|Rachaad White|
Brock Purdy|K.C. Concepcion|Jaxson Dart|Wan'Dale Robinson|
Josh Jacobs|Bo Nix|Dallas Goedert|Harold Fannin|
Xavier Worthy|Kenneth Gainwell|Patrick Mahomes|Jayden Reed|
Jared Goff|MarShawn Lloyd|Jordyn Tyson|Kyle Pitts|
Aaron Jones|Matthew Stafford|Jakobi Meyers|Denzel Boston|
Chris Rodriguez|Travis Kelce|Woody Marks|Keenan Allen|
Tyler Allgeier|Tyler Shough|Jordan Love|Romeo Doubs|
Mike Washington Jr.|Baker Mayfield|Jonah Coleman|
Kyler Murray|Juwan Johnson|Caleb Douglas|Khalil Shakir|
Kaelon Black|Devin Singletary|Jake Ferguson|Mark Andrews|
Malik Willis|Rashid Shaheed|Keaton Mitchell|Tank Bigsby|
Travis Hunter|De'Zhaun Stribling|Brenton Strange"""

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

names = [x.strip() for x in C.replace("\n", "").split("|")
         if x.strip()]
CR = {norm(n): i + 1 for i, n in enumerate(names)}
print("consensus list parsed: %d players" % len(CR))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
col = "mvorp" if "mvorp" in B.columns else "vorp"
B[col] = pd.to_numeric(B[col], errors="coerce")
B = B[B[col].notna()].copy()
B["m_rank"] = B[col].rank(ascending=False, method="min")
B["c_rank"] = B["k"].map(CR)
hit = int(B["c_rank"].notna().sum())
print("matched to our board: %d of %d" % (hit, len(CR)))
miss = [n for n in names if norm(n) not in set(B["k"])]
if miss:
    print("unmatched:", miss[:10])

# players off the consensus list sit behind it, ordered
# by the model
tail = len(CR) + 1
B["c_rank"] = B["c_rank"].fillna(
    tail + B["m_rank"] / 20.0)
B["blend"] = (W_CONS * B["c_rank"]
              + (1 - W_CONS) * B["m_rank"])
B = B.sort_values("blend")
B["rank_v"] = range(1, len(B) + 1)
B["pre_rank"] = B["rank_v"]
B["upd_rank"] = B["rank_v"]
B["pre_vorp"] = B[col]
B["upd_vorp"] = B[col]
B.drop(columns=["k"]).to_csv("board_final.csv",
                             index=False)

print("\n=== TOP 30 ===")
print("%-3s %-24s %-4s %7s %7s"
      % ("#", "PLAYER", "POS", "CONS", "MODEL"))
for _, r in B.head(30).iterrows():
    print("%-3d %-24s %-4s %7.0f %7.0f"
          % (r["rank_v"], r["player_display_name"][:24],
             r["position"], r["c_rank"], r["m_rank"]))

print("\n=== WHERE THE MODEL DISAGREES MOST ===")
z = B.head(120).copy()
z["gap"] = z["m_rank"] - z["c_rank"]
for _, r in z.reindex(z["gap"].abs().sort_values(
        ascending=False).index).head(10).iterrows():
    print("  %-24s consensus #%-4.0f model #%-4.0f -> #%d"
          % (r["player_display_name"][:24], r["c_rank"],
             r["m_rank"], r["rank_v"]))
