import pandas as pd, re, io

ADP = """Jahmyr Gibbs|1.7
Bijan Robinson|1.8
Puka Nacua|3.1
Ja'Marr Chase|3.9
Jaxon Smith-Njigba|5.4
Amon-Ra St. Brown|6.3
Christian McCaffrey|6.5
Jonathan Taylor|7.4
Drake London|9.9
De'Von Achane|10.2
CeeDee Lamb|10.6
Justin Jefferson|11.7
James Cook III|12.6
Chase Brown|13.4
Rashee Rice|14.9
Ashton Jeanty|15.2
Derrick Henry|17.5
A.J. Brown|18.1
George Pickens|19.4
Saquon Barkley|20.0
Chris Olave|20.5
Nico Collins|21.5
Kenneth Walker|22.3
Omarion Hampton|22.6
Zay Flowers|24.9
Garrett Wilson|26.1
Malik Nabers|27.3
Jeremiyah Love|28.7
Trey McBride|28.7
DeVonta Smith|29.3
Josh Jacobs|31.1
Kyren Williams|31.3
Tetairoa McMillan|33.4
Josh Allen|33.5
Breece Hall|34.0
Cam Skattebo|34.8
Brock Bowers|35.8
Tee Higgins|36.1
Javonte Williams|36.7
Emeka Egbuka|37.0
Ladd McConkey|37.5
Travis Etienne Jr.|41.2
Davante Adams|41.5
Jameson Williams|43.9
Bucky Irving|45.7
D'Andre Swift|45.9
Jaylen Waddle|46.1
Terry McLaurin|46.5
DJ Moore|49.4
Rome Odunze|49.9
Quinshon Judkins|51.3
Drake Maye|51.6
Mike Evans|53.1
Bhayshul Tuten|53.2
Colston Loveland|56.7
Lamar Jackson|57.0
Joe Burrow|57.1
David Montgomery|58.1
Christian Watson|58.6
Alec Pierce|59.4
Jaylen Warren|60.0
TreVeyon Henderson|60.2
Luther Burden III|60.3
Courtland Sutton|60.5
Tyler Warren|64.7
DK Metcalf|65.0
Parker Washington|65.1
Dak Prescott|65.5
Marvin Harrison Jr.|66.4
Tony Pollard|67.5
Rhamondre Stevenson|70.3
Brian Thomas Jr.|71.9
Jayden Daniels|73.1
Carnell Tate|74.5
Michael Pittman Jr.|74.8
Chuba Hubbard|75.3
Rico Dowdle|75.3
Kyle Pitts Sr.|76.1
Michael Wilson|76.6
Matthew Stafford|77.3
Harold Fannin Jr.|79.2
Jalen Hurts|80.5
Chris Godwin Jr.|80.9
Jadarian Price|81.1
Josh Downs|82.0
RJ Harvey|82.8
Wan'Dale Robinson|85.9
Brock Purdy|88.8
Caleb Williams|88.9
Jakobi Meyers|88.9
Kenny Gainwell|90.0
Sam LaPorta|90.6
Stefon Diggs|91.5
Trevor Lawrence|92.7
Quentin Johnston|93.3
J.K. Dobbins|94.4
Jayden Reed|94.6
Jordan Addison|98.1
Keon Coleman|98.6
Aaron Jones Sr.|100.3
Jared Goff|100.6
Khalil Shakir|101.1
Patrick Mahomes|101.3
Tucker Kraft|104.0
Jonathon Brooks|105.4
Justin Herbert|106.2
Xavier Worthy|106.8
Jordyn Tyson|107.3
Rachaad White|107.7
Matthew Golden|107.8
Dallas Goedert|108.2
Travis Kelce|109.4
Kyle Monangai|112.5
Romeo Doubs|112.8
Deebo Samuel Sr.|113.6
Bo Nix|114.0
Makai Lemon|114.9
Jacory Croskey-Merritt|117.6
Jaxson Dart|117.9
George Kittle|118.5
Blake Corum|120.8
Jordan Mason|121.1
Jalen Coker|121.3
KC Concepcion|121.8
Jerry Jeudy|127.3"""

def norm(s):
    s = str(s).lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    return re.sub(r"[^a-z]", "", s)

adp = pd.read_csv(io.StringIO(ADP), sep="|", names=["player", "adp"])
adp["key"] = adp["player"].map(norm)
adp["adp_rank"] = adp["adp"].rank(method="min")
adp.to_csv("adp_2026.csv", index=False)

b = pd.read_csv("board_v5.csv", low_memory=False)
b["key"] = b["player_display_name"].map(norm)
b = b.merge(adp[["key", "adp", "adp_rank"]], on="key", how="left")
print(f"ADP matched: {b['adp'].notna().sum()} of {len(adp)}")
print("unmatched:", sorted(set(adp['key']) - set(b['key'])))

ecr = b["ecr"] if "ecr" in b.columns else None
b["model_rank"] = b["value"].rank(ascending=False, method="min")
b["market_rank"] = b["adp_rank"]
if ecr is not None:
    b["market_rank"] = b["market_rank"].fillna(b["ecr"].rank(method="min"))

hasmkt = b["market_rank"].notna()
b["blend"] = b["model_rank"]
b.loc[hasmkt, "blend"] = 0.5 * b.loc[hasmkt, "model_rank"] + 0.5 * b.loc[hasmkt, "market_rank"]
b["source_mkt"] = hasmkt.map({True: "market", False: "model_only"})

b = b.sort_values("blend").reset_index(drop=True)
b["rank"] = b.index + 1
b["pos_rank"] = b.groupby("position")["blend"].rank(method="min").astype(int)
b["disagree"] = b["model_rank"] - b["market_rank"]
b.to_csv("board_v6.csv", index=False)

cols = ["rank", "player_display_name", "position", "pos_rank", "team",
        "points", "exp_games", "model_rank", "adp", "blend"]
print("\n=== BOARD v6 (50/50 model + market): TOP 40 ===")
print(b.head(40)[cols].round(1).to_string(index=False))

d = b[b["market_rank"].notna() & (b["model_rank"] <= 200)]
print("\n=== We're HIGHEST on (model likes, market doesn't) ===")
print(d.nsmallest(12, "disagree")[
    ["player_display_name", "position", "model_rank", "adp", "disagree"]].round(1).to_string(index=False))
print("\n=== We're LOWEST on (market likes, model doesn't) ===")
print(d.nlargest(12, "disagree")[
    ["player_display_name", "position", "model_rank", "adp", "disagree"]].round(1).to_string(index=False))
print("\nSaved board_v6.csv and adp_2026.csv")
