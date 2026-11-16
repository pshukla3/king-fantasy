import numpy as np
import pandas as pd
import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

NEED = ["game_id", "season", "posteam", "home_team",
        "away_team", "score_differential",
        "game_seconds_remaining",
        "half_seconds_remaining", "down", "ydstogo",
        "yardline_100", "posteam_timeouts_remaining",
        "defteam_timeouts_remaining", "spread_line",
        "result", "qtr", "play_type"]

print("probing 2025 pbp for schema...")
S = pl(nfl.load_pbp(seasons=[2025]))
print("rows %d | cols %d" % (len(S), len(S.columns)))
print("\n=== COLUMN CHECK ===")
HAVE = []
for c in NEED:
    ok = c in S.columns
    print("  %-30s %s" % (c, "yes" if ok else "MISSING"))
    if ok:
        HAVE.append(c)
print("\nusable: %d of %d" % (len(HAVE), len(NEED)))
d = S[S["down"].notna()] if "down" in S.columns else S
print("plays with a down: %d" % len(d))
if "result" in S.columns:
    print("result range: %.0f to %.0f"
          % (S["result"].min(), S["result"].max()))

YRS = list(range(2015, 2026))
print("\n=== BUILDING %d-%d ===" % (YRS[0], YRS[-1]))
out = []
for y in YRS:
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in HAVE if c in d.columns]].copy()
    out.append(d)
    print("  %d  %6d plays" % (y, len(d)))
P = pd.concat(out, ignore_index=True)
del out
print("raw %d" % len(P))

P = P[P["posteam"].notna()]
P = P[P["down"].notna()]
P = P[P["qtr"] <= 4]
P = P[P["game_seconds_remaining"] > 0]
P = P[P["result"].notna() & (P["result"] != 0)]
for c in ["score_differential", "game_seconds_remaining",
          "half_seconds_remaining", "down", "ydstogo",
          "yardline_100", "posteam_timeouts_remaining",
          "defteam_timeouts_remaining", "spread_line",
          "result"]:
    if c in P.columns:
        P[c] = pd.to_numeric(P[c], errors="coerce")
P = P.dropna(subset=["score_differential",
                     "game_seconds_remaining",
                     "yardline_100"])

home = P["posteam"] == P["home_team"]
P["win"] = np.where(home, (P["result"] > 0).astype(int),
                    (P["result"] < 0).astype(int))
P["spread_pos"] = np.where(home, P["spread_line"],
                           -P["spread_line"])
P["spread_pos"] = P["spread_pos"].fillna(0.0)
t = P["game_seconds_remaining"].clip(lower=1)
P["t"] = t
P["expt"] = np.exp(-4.0 * t / 3600.0)
P["sd_t"] = P["score_differential"] / np.sqrt(t / 60.0 + 1)
P["to_diff"] = (P["posteam_timeouts_remaining"]
                - P["defteam_timeouts_remaining"])
P["is4"] = (P["down"] == 4).astype(int)
P["half"] = P["half_seconds_remaining"].fillna(t)

K = ["season", "game_id", "win", "score_differential",
     "sd_t", "t", "expt", "half", "down", "ydstogo",
     "yardline_100", "to_diff", "spread_pos", "is4"]
P[K].to_csv("wp_train.csv", index=False)
print("\nwrote wp_train.csv: %d plays | %d games"
      % (len(P), P["game_id"].nunique()))
print("base rate posteam wins: %.4f" % P["win"].mean())
print("\nsanity, win rate by score diff bucket:")
for lo, hi in [(-99, -17), (-16, -9), (-8, -1),
               (0, 0), (1, 8), (9, 16), (17, 99)]:
    d = P[(P["score_differential"] >= lo)
          & (P["score_differential"] <= hi)]
    if len(d):
        print("  %+4d..%+4d  n=%7d  win %.3f"
              % (lo, hi, len(d), d["win"].mean()))

YRS = list(range(2015, 2026))
print("\n=== BUILDING %d-%d ===" % (YRS[0], YRS[-1]))
out = []
for y in YRS:
    d = pl(nfl.load_pbp(seasons=[y]))
    d = d[[c for c in HAVE if c in d.columns]].copy()
    out.append(d)
    print("  %d  %6d plays" % (y, len(d)))
P = pd.concat(out, ignore_index=True)
del out
print("raw %d" % len(P))

P = P[P["posteam"].notna()]
P = P[P["down"].notna()]
P = P[P["qtr"] <= 4]
P = P[P["game_seconds_remaining"] > 0]
P = P[P["result"].notna() & (P["result"] != 0)]
for c in ["score_differential", "game_seconds_remaining",
          "half_seconds_remaining", "down", "ydstogo",
          "yardline_100", "posteam_timeouts_remaining",
          "defteam_timeouts_remaining", "spread_line",
          "result"]:
    if c in P.columns:
        P[c] = pd.to_numeric(P[c], errors="coerce")
P = P.dropna(subset=["score_differential",
                     "game_seconds_remaining",
                     "yardline_100"])

home = P["posteam"] == P["home_team"]
P["win"] = np.where(home, (P["result"] > 0).astype(int),
                    (P["result"] < 0).astype(int))
P["spread_pos"] = np.where(home, P["spread_line"],
                           -P["spread_line"])
P["spread_pos"] = P["spread_pos"].fillna(0.0)
t = P["game_seconds_remaining"].clip(lower=1)
P["t"] = t
P["expt"] = np.exp(-4.0 * t / 3600.0)
P["sd_t"] = P["score_differential"] / np.sqrt(t / 60.0 + 1)
P["to_diff"] = (P["posteam_timeouts_remaining"]
                - P["defteam_timeouts_remaining"])
P["is4"] = (P["down"] == 4).astype(int)
P["half"] = P["half_seconds_remaining"].fillna(t)

K = ["season", "game_id", "win", "score_differential",
     "sd_t", "t", "expt", "half", "down", "ydstogo",
     "yardline_100", "to_diff", "spread_pos", "is4"]
P[K].to_csv("wp_train.csv", index=False)
print("\nwrote wp_train.csv: %d plays | %d games"
      % (len(P), P["game_id"].nunique()))
print("base rate posteam wins: %.4f" % P["win"].mean())
print("\nsanity, win rate by score diff bucket:")
for lo, hi in [(-99, -17), (-16, -9), (-8, -1),
               (0, 0), (1, 8), (9, 16), (17, 99)]:
    d = P[(P["score_differential"] >= lo)
          & (P["score_differential"] <= hi)]
    if len(d):
        print("  %+4d..%+4d  n=%7d  win %.3f"
              % (lo, hi, len(d), d["win"].mean()))
