import pandas as pd, numpy as np

inj = pd.read_csv("injuries_raw.csv", low_memory=False)
H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)
PTS = "ppr_points" if "ppr_points" in H.columns else "fantasy_points_ppr"
print("points col:", PTS)

inj = inj[inj["position"].isin(["QB", "RB", "WR", "TE"])].copy()
inj = inj[inj["report_status"].astype(str).str.strip().eq("Out")]
inj["inj"] = (inj["report_primary_injury"].astype(str)
              .str.replace(r"^(right|left|Right|Left)\s+", "", regex=True)
              .str.strip().str.title())
inj = inj[~inj["inj"].str.contains("Not Injury|Personal|Nan|Illness", na=True)]
inj = inj.dropna(subset=["week", "season"])
inj = inj.drop_duplicates(subset=["gsis_id", "season", "week"])
inj["week"] = inj["week"].astype(int)
inj["season"] = inj["season"].astype(int)
print("unique player-weeks OUT:", len(inj))

inj = inj.sort_values(["gsis_id", "season", "week"])
gap = inj.groupby(["gsis_id", "season"])["week"].diff().fillna(99)
inj["spell"] = (gap != 1).cumsum()

sp = inj.groupby("spell").agg(
    gsis_id=("gsis_id", "first"), season=("season", "first"),
    position=("position", "first"),
    start=("week", "min"), end=("week", "max"), weeks_out=("week", "size"),
    inj=("inj", lambda s: s.mode().iat[0])).reset_index(drop=True)
print("injury spells:", len(sp))

W = H[["player_id", "season", "week", PTS]].rename(columns={"player_id": "gsis_id"})

def window(row, lo, hi, season_off=0):
    m = W[(W["gsis_id"] == row["gsis_id"]) & (W["season"] == row["season"] + season_off) &
          (W["week"] >= lo) & (W["week"] <= hi)]
    return m[PTS].mean() if len(m) >= 2 else np.nan

sp["pre"] = sp.apply(lambda r: window(r, 1, r["start"] - 1), axis=1)
sp["back4"] = sp.apply(lambda r: window(r, r["end"] + 1, r["end"] + 4), axis=1)
sp["next_yr"] = sp.apply(lambda r: window(r, 1, 18, 1), axis=1)
sp.to_csv("injury_spells.csv", index=False)

sp["ret_ratio"] = sp["back4"] / sp["pre"]
sp["nxt_ratio"] = sp["next_yr"] / sp["pre"]
sp = sp[sp["pre"] >= 5]

t = sp.groupby("inj").agg(
    n=("weeks_out", "size"),
    med_out=("weeks_out", "median"),
    p75_out=("weeks_out", lambda x: x.quantile(0.75)),
    pre_ppg=("pre", "mean"),
    ret_pct=("ret_ratio", "median"),
    nxt_pct=("nxt_ratio", "median")).reset_index()
t = t[t["n"] >= 12].sort_values("n", ascending=False)

print("\n=== INJURY EFFECT TABLE (skill players, 2016-2025) ===")
print("med_out = weeks missed | ret_pct = PPG first 4 games back vs before")
print("nxt_pct = PPG next season vs before injury\n")
print(t.round(2).to_string(index=False))
t.to_csv("injury_effects.csv", index=False)

print("\n=== ACHILLES specifically (Kittle's injury) ===")
a = sp[sp["inj"].str.contains("Achilles", na=False)]
print(f"n={len(a)}  median weeks out={a['weeks_out'].median():.1f}  "
      f"return PPG ratio={a['ret_ratio'].median():.2f}  "
      f"next-season ratio={a['nxt_ratio'].median():.2f}")
print("\nSaved injury_effects.csv and injury_spells.csv")
