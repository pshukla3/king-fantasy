
import pandas as pd

sch = pd.read_csv("schedules.csv", low_memory=False)

s26 = sch[sch["season"] == 2026]

print("=== 2026 schedule: forward-looking market data ===")

print("games:", len(s26))

for c in ["total_line", "spread_line", "away_moneyline", "home_moneyline", "away_qb_name", "home_qb_name"]:

    if c in s26.columns:

        print(f"  {c:16s} non-null: {s26[c].notna().sum():4d} / {len(s26)}")

rost = pd.read_csv("rosters_2026.csv", low_memory=False)

print("\n=== 2026 rosters: rookie / draft capital ===")

for c in ["draft_number", "rookie_year", "entry_year", "years_exp", "depth_chart_position", "status"]:

    if c in rost.columns:

        print(f"  {c:22s} non-null: {rost[c].notna().sum():4d} / {len(rost)}")

rk = rost[rost["rookie_year"] == 2026] if "rookie_year" in rost.columns else rost.iloc[0:0]

print("  2026 rookies on rosters:", len(rk))

if len(rk):

    print(rk[rk["position"].isin(["QB", "RB", "WR", "TE"])].nsmallest(

        10, "draft_number")[["full_name", "position", "team", "draft_number"]].to_string(index=False))

print("\n=== Team changes 2025 -> 2026 (skill players) ===")

H = pd.read_csv("weekly_stats_long_history.csv", low_memory=False)

last = H[H["season"] == 2025].sort_values("week").groupby("player_id").tail(1)[

    ["player_id", "player_display_name", "position", "team"]].rename(columns={"team": "team_2025"})

cur = rost[["gsis_id", "team"]].dropna(subset=["gsis_id"]).drop_duplicates("gsis_id").rename(

    columns={"gsis_id": "player_id", "team": "team_2026"})

mv = last.merge(cur, on="player_id", how="inner")

mv = mv[(mv["team_2025"] != mv["team_2026"]) & mv["position"].isin(["QB", "RB", "WR", "TE"])]

print("skill players who changed teams:", len(mv))

print(mv.head(20).to_string(index=False))

print("\n=== Late-season usage shift (2025 wk13-18 vs full season, WR) ===")

w = H[(H["season"] == 2025) & (H["position"] == "WR")]

full = w.groupby("player_id")["targets"].mean().rename("tgt_full")

late = w[w["week"] >= 13].groupby("player_id")["targets"].mean().rename("tgt_late")

gm = w.groupby("player_id").size().rename("g")

t = pd.concat([full, late, gm], axis=1).reset_index()

t = t[t["g"] >= 10].merge(last[["player_id", "player_display_name"]], on="player_id")

t["delta"] = t["tgt_late"] - t["tgt_full"]

print(t.nlargest(10, "delta")[["player_display_name", "tgt_full", "tgt_late", "delta"]].round(2).to_string(index=False))

