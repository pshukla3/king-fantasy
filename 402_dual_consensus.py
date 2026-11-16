import re
import numpy as np
import pandas as pd

FP = """Jahmyr Gibbs|Ja'Marr Chase|Bijan Robinson|Puka Nacua|
Jaxon Smith-Njigba|Amon-Ra St. Brown|Jonathan Taylor|
James Cook|Christian McCaffrey|CeeDee Lamb|A.J. Brown|
Justin Jefferson|Nico Collins|Saquon Barkley|Derrick Henry|
Drake London|Chase Brown|George Pickens|Kenneth Walker III|
Trey McBride|Omarion Hampton|De'Von Achane|Chris Olave|
Josh Allen|Malik Nabers|Ashton Jeanty|DeVonta Smith|
Lamar Jackson|Zay Flowers|Colston Loveland|Kyren Williams|
Javonte Williams|Brock Bowers|Tee Higgins|Drake Maye|
Rashee Rice|Emeka Egbuka|Breece Hall|Tetairoa McMillan|
Jaylen Waddle|Ladd McConkey|Joe Burrow|Travis Etienne|
Jeremiyah Love|D'Andre Swift|Jameson Williams|Davante Adams|
Garrett Wilson|Christian Watson|Bucky Irving|Terry McLaurin|
Jalen Hurts|David Montgomery|Quinshon Judkins|
Luther Burden III|Cam Skattebo|DJ Moore|Tyler Warren|
Rome Odunze|Jayden Daniels|Jadarian Price|Tucker Kraft|
Bhayshul Tuten|Mike Evans|Caleb Williams|Parker Washington|
Rhamondre Stevenson|Justin Herbert|Trevor Lawrence|
Marvin Harrison Jr.|TreVeyon Henderson|Jaylen Warren|
Dak Prescott|DK Metcalf|Brian Thomas Jr.|Tony Pollard|
Rico Dowdle|Sam LaPorta|Carnell Tate|Blake Corum|
J.K. Dobbins|Quentin Johnston|Alec Pierce|George Kittle|
Courtland Sutton|Jonathon Brooks|Kyle Pitts|
Chris Godwin Jr.|Harold Fannin|Jacory Croskey-Merritt|
Jordan Mason|Brock Purdy|MarShawn Lloyd|Chuba Hubbard|
Bo Nix|Michael Wilson|Jaxson Dart|Dalton Kincaid|
Jayden Reed|Jordan Addison"""

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

fp = [x.strip() for x in FP.replace("\n", "").split("|")
      if x.strip()]
FPR = {norm(n): i + 1 for i, n in enumerate(fp)}
src = open("400_consensus.py").read()
blk = re.search(r'C = """(.*?)"""', src, re.S).group(1)
fl = [x.strip() for x in blk.replace("\n", "").split("|")
      if x.strip()]
FLR = {norm(n): i + 1 for i, n in enumerate(fl)}
print("fantasypros %d | flock %d" % (len(FPR), len(FLR)))

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
col = "mvorp" if "mvorp" in B.columns else "vorp"
B[col] = pd.to_numeric(B[col], errors="coerce")
B["m_rank"] = B[col].rank(ascending=False, method="min")
B["fp_r"] = B["k"].map(FPR)
B["fl_r"] = B["k"].map(FLR)

# average the two experts where both have an opinion
B["cons"] = B[["fp_r", "fl_r"]].mean(axis=1)
n_both = int((B["fp_r"].notna() & B["fl_r"].notna()).sum())
n_any = int(B["cons"].notna().sum())
print("on both lists: %d | on at least one: %d"
      % (n_both, n_any))
d = B[B["fp_r"].notna() & B["fl_r"].notna()]
print("the two experts agree: rho %.3f"
      % d["fp_r"].corr(d["fl_r"], method="spearman"))
print("we agree with them   : rho %.3f"
      % d["cons"].corr(d["m_rank"], method="spearman"))

tail = float(B["cons"].max() or 100)

# K and DST have no consensus entry in the transcribed
# lists, but both sources place DST1 at 154 and K1 at 179.
# anchor them there, ordered within position by our value.
for pos, start in (("DST", 154), ("K", 179)):
    m = B["position"] == pos
    r = B.loc[m, col].rank(ascending=False, method="min")
    B.loc[m, "cons"] = start + (r - 1) * 2.0

B["cons_f"] = B["cons"].fillna(tail + B["m_rank"] / 8.0)

# the model adjusts consensus but cannot overrule it:
# a player on an expert list moves at most 20 spots.
CAP = 20.0
delta = (B["m_rank"] - B["cons_f"]).clip(-CAP, CAP)
onlist = B["cons"].notna()
B["blend"] = B["cons_f"] + 0.35 * delta
B.loc[~onlist, "blend"] = (0.65 * B.loc[~onlist, "cons_f"]
                           + 0.35 * B.loc[~onlist, "m_rank"])
B = B.sort_values("blend")
B["rank_v"] = range(1, len(B) + 1)
B["pre_rank"] = B["rank_v"]
B["upd_rank"] = B["rank_v"]
B["pre_vorp"] = B[col]
B["upd_vorp"] = B[col]
B.drop(columns=["k"]).to_csv("board_final.csv",
                             index=False)

print("\n=== TOP 25 ===")
print("%-3s %-24s %-5s %5s %5s %6s"
      % ("#", "PLAYER", "POS", "FP", "FLOCK", "OURS"))
for _, r in B.head(25).iterrows():
    print("%-3d %-24s %-5s %5s %5s %6.0f"
          % (r["rank_v"], r["player_display_name"][:24],
             r["position"],
             "-" if pd.isna(r["fp_r"]) else int(r["fp_r"]),
             "-" if pd.isna(r["fl_r"]) else int(r["fl_r"]),
             r["m_rank"]))
print("\n=== FIRST AT EACH POSITION ===")
seen = set()
for _, r in B.iterrows():
    p = r["position"]
    if p not in seen:
        seen.add(p)
        print("  %-4s #%-4d %s"
              % (p, r["rank_v"],
                 r["player_display_name"][:24]))
