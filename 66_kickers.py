import pandas as pd
import nflreadpy as nfl

SEASONS = [2023, 2024, 2025]
print("pulling play-by-play for %s (this takes a minute) ..." % SEASONS)
P = nfl.load_pbp(seasons=SEASONS)
P = P.to_pandas() if hasattr(P, "to_pandas") else P
print("pbp rows: %d" % len(P))

KN = next((c for c in ["kicker_player_name", "kicker_player_display_name"]
           if c in P.columns), None)
print("kicker col: %s" % KN)
need = ["field_goal_attempt", "field_goal_result", "kick_distance",
        "extra_point_attempt", "extra_point_result", "game_id"]
print("missing: %s" % [c for c in need if c not in P.columns])

fg = P[(P["field_goal_attempt"] == 1) & P[KN].notna()].copy()
fg["made"] = (fg["field_goal_result"] == "made").astype(int)
fg["dist"] = pd.to_numeric(fg["kick_distance"], errors="coerce")
fg = fg.dropna(subset=["dist"])
print("FG attempts: %d" % len(fg))

BINS = [0, 29, 39, 49, 59, 99]
LAB = ["<30", "30-39", "40-49", "50-59", "60+"]
PTS = {"<30": 3, "30-39": 3, "40-49": 4, "50-59": 5, "60+": 5}
fg["band"] = pd.cut(fg["dist"], bins=BINS, labels=LAB)

print("\n=== LEAGUE FG ACCURACY BY DISTANCE (2023-2025) ===")
lg = fg.groupby("band", observed=True)["made"].agg(att="size", pct="mean").reset_index()
lg["pts_per_att"] = lg["band"].map(PTS) * lg["pct"]
print(lg.round(3).to_string(index=False))
fg.to_csv("fg_attempts.csv", index=False)
print("\nSaved fg_attempts.csv")

t = fg.pivot_table(index=KN, columns="band", values="made",
                   aggfunc=["size", "mean"], observed=True)
att, pct = t["size"].fillna(0), t["mean"]

gm = fg.groupby(KN)["game_id"].nunique().rename("gms")
tot = fg.groupby(KN)["made"].agg(fga="size", fgm="sum")

xp = P[(P["extra_point_attempt"] == 1) & P[KN].notna()].copy()
xp["made"] = (xp["extra_point_result"] == "good").astype(int)
xpa = xp.groupby(KN)["made"].agg(xpa="size", xpm="sum")

K = pd.concat([tot, xpa, gm], axis=1).fillna(0)
K["fg_pct"] = K["fgm"] / K["fga"].replace(0, float("nan"))
K["fg_pg"] = K["fga"] / K["gms"]

pts = pd.Series(0.0, index=att.index)
for b in att.columns:
    pts = pts.add(att[b] * pct[b].fillna(0) * PTS.get(b, 3), fill_value=0)
K["fg_pts"] = pts
K["ppg"] = (K["fg_pts"] + K["xpm"]) / K["gms"]

K = K[K["gms"] >= 16].sort_values("ppg", ascending=False)
show = K.head(30).copy()
for b in LAB:
    if b in att.columns:
        a = att[b].reindex(show.index).fillna(0).astype(int).astype(str)
        p = (pct[b].reindex(show.index) * 100).round(0).fillna(0).astype(int).astype(str)
        show[b] = a + "/" + p + "%"

cols = ["gms", "fga", "fg_pct", "fg_pg", "xpm", "ppg"] + [b for b in LAB if b in show.columns]
print("\n\n=== KICKER RANKINGS — projected PPG (min 16 games) ===")
print("  distance cols show attempts/make%%\n")
print(show[cols].round(2).to_string())

K.reset_index().rename(columns={KN: "kicker"}).to_csv("kicker_projections.csv", index=False)

print("\n\n=== IS ACCURACY OR VOLUME THE REAL SIGNAL? ===")
print("  spread in fg_pct : %.3f to %.3f" % (K["fg_pct"].min(), K["fg_pct"].max()))
print("  spread in fg_pg  : %.2f to %.2f" % (K["fg_pg"].min(), K["fg_pg"].max()))
print("  corr(fg_pct, ppg) = %.3f" % K["fg_pct"].corr(K["ppg"]))
print("  corr(fg_pg,  ppg) = %.3f" % K["fg_pg"].corr(K["ppg"]))

print("\n=== YOUR K: Harrison Butker ===")
b = K[K.index.astype(str).str.contains("Butker", na=False)]
print(b[cols].round(2).to_string() if len(b) else "  not found")
print("\nSaved kicker_projections.csv")
