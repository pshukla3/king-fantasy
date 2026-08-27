import pandas as pd, re, os

SEED = [
    ("Ricky Pearsall",    0.00, 1.00, "PCL surgery, IR - out 2026"),
    ("Jayden Higgins",    0.00, 1.00, "torn ACL - out 2026"),
    ("George Kittle",     0.88, 0.75, "Achilles Jan 11, PUP; measured nxt_pct 0.66"),
    ("Sam LaPorta",       0.85, 0.85, "hip; 2025 back surgery"),
    ("Tyler Warren",      0.92, 0.95, "groin, back soon"),
    ("Luther Burden III", 0.88, 0.95, "groin, misses preseason"),
]
if not os.path.exists("news_overrides_v2.csv"):
    pd.DataFrame(SEED, columns=["player", "games_mult", "points_mult", "note"]).to_csv(
        "news_overrides_v2.csv", index=False)
    print("created news_overrides_v2.csv - edit as news breaks")
ov = pd.read_csv("news_overrides_v2.csv")
print(ov.to_string(index=False))

def norm(s):
    s = str(s).lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", s)
    return re.sub(r"[^a-z]", "", s)

b = pd.read_csv("board_v4.csv", low_memory=False)
b["key"] = b["player_display_name"].map(norm)
ov["key"] = ov["player"].map(norm)
b = b.merge(ov[["key", "games_mult", "points_mult", "note"]], on="key", how="left")
b["games_mult"] = b["games_mult"].fillna(1.0)
b["points_mult"] = b["points_mult"].fillna(1.0)

b["exp_games"] = b["exp_games"] * b["games_mult"]
b["points"] = b["points"] * b["points_mult"]
b["vorp"] = b["points"] - b["position"].map(
    b.groupby("position").apply(lambda g: g["points"].sub(g["vorp"]).median()))
b["value"] = b["exp_games"] * b["vorp"] * b["reliability"]
b["model_rank"] = b["value"].rank(ascending=False, method="min")

adp = pd.read_csv("adp_2026.csv")
adp["key"] = adp["player"].map(norm)
b = b.merge(adp[["key", "adp", "adp_rank"]], on="key", how="left")
b["market_rank"] = b["adp_rank"]
hasm = b["market_rank"].notna()
b["blend"] = b["model_rank"]
b.loc[hasm, "blend"] = 0.5 * b.loc[hasm, "model_rank"] + 0.5 * b.loc[hasm, "market_rank"]

kd = pd.read_csv("board_v7.csv", low_memory=False)
kd = kd[kd["position"].isin(["K", "DST"])]
cols = ["player_id", "player_display_name", "position", "team", "points",
        "exp_games", "value", "adp", "model_rank", "market_rank", "blend"]
allp = pd.concat([b.reindex(columns=cols), kd.reindex(columns=cols)], ignore_index=True)
allp = allp.sort_values("blend").reset_index(drop=True)
allp["rank"] = allp.index + 1
allp["pos_rank"] = allp.groupby("position")["blend"].rank(method="min").astype(int)
allp.to_csv("board_final.csv", index=False)

print("\n=== players moved by injury overrides ===")
m = b[b["games_mult"].lt(1.0) | b["points_mult"].lt(1.0)]
print(m[["player_display_name", "position", "points", "exp_games",
         "model_rank", "blend"]].round(1).to_string(index=False))

print("\n=== BOARD FINAL: TOP 40 ===")
print(allp.head(40)[["rank", "player_display_name", "position", "pos_rank",
                     "team", "points", "exp_games", "adp", "blend"]].round(1).to_string(index=False))
print("\nSaved board_final.csv")
