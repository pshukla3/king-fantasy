import json, re, ssl, certifi
import urllib.request as U
import numpy as np
import nflreadpy as nfl

CTX = ssl.create_default_context(cafile=certifi.where())

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

print("=== 1. CURRENT NFL KICKERS (Sleeper roster) ===")
ALL = json.loads(U.urlopen(U.Request(
    "https://api.sleeper.app/v1/players/nfl",
    headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60, context=CTX).read())
K = []
for pid, p in ALL.items():
    if not isinstance(p, dict):
        continue
    if p.get("position") != "K" or not p.get("team"):
        continue
    K.append({"n": p.get("full_name"), "tm": p.get("team"),
              "age": p.get("age"), "yrs": p.get("years_exp"),
              "sid": pid, "gsis": p.get("gsis_id"),
              "srank": p.get("search_rank"),
              "status": p.get("status"),
              "inj": p.get("injury_status")})
K.sort(key=lambda x: (x["tm"] or "", x["n"] or ""))
print("kickers on an active roster: %d" % len(K))
print("%-24s %-5s %-5s %-5s %s"
      % ("KICKER", "TEAM", "AGE", "EXP", "STATUS"))
for k in K:
    print("%-24s %-5s %-5s %-5s %s"
          % ((k["n"] or "")[:24], k["tm"], k["age"] or "-",
             k["yrs"] if k["yrs"] is not None else "-",
             (k["inj"] or k["status"] or "")))
json.dump(K, open("kickers_roster.json", "w"), indent=1)
print("-> kickers_roster.json")

YR = list(range(2016, 2027))
print("\n=== 2. TEN YEARS OF KICKER STATS ===")
d = nfl.load_player_stats(YR).to_pandas()
kc = [c for c in d.columns
      if any(t in c.lower() for t in
             ("fg", "pat", "kick", "xp", "field"))]
print("kicking columns in player_stats:")
print("  " + ", ".join(kc) if kc else "  NONE FOUND")
kk = d[d["position"] == "K"]
print("K rows %d | players %d | seasons %s-%s"
      % (len(kk), kk["player_id"].nunique(),
         kk["season"].min(), kk["season"].max()))
if kc:
    print("\nsample row:")
    s = kk[kk[kc[0]].notna()].head(1)
    for c in ["player_display_name", "season", "week",
              "team"] + kc[:10]:
        if c in s.columns and len(s):
            print("  %-28s %s" % (c, s.iloc[0][c]))

print("\n=== 3. FIELD GOALS FROM PLAY-BY-PLAY ===")
print("(loading pbp, this takes a minute)")
p = nfl.load_pbp(list(range(2019, 2027))).to_pandas()
fg = p[p["field_goal_attempt"] == 1].copy()
fg["dist"] = fg["kick_distance"]
fg = fg[fg["dist"].notna()]
print("field goal attempts: %d  (%s-%s)"
      % (len(fg), int(fg["season"].min()),
         int(fg["season"].max())))
print("\nmake rate by distance band:")
bands = [(0, 19), (20, 29), (30, 39), (40, 49),
         (50, 59), (60, 99)]
for lo, hi in bands:
    s = fg[(fg["dist"] >= lo) & (fg["dist"] <= hi)]
    if not len(s):
        continue
    made = (s["field_goal_result"] == "made").mean()
    print("  %2d-%-2d yds  %6d att   %5.1f%% made"
          % (lo, hi, len(s), made * 100))
cols = [c for c in ("kicker_player_name", "kicker_player_id",
                    "kick_distance", "field_goal_result",
                    "posteam", "season", "week", "weather",
                    "roof", "surface", "temp", "wind")
        if c in fg.columns]
print("\npbp columns we can use: %s" % ", ".join(cols))
fg[cols].to_csv("fg_attempts.csv", index=False)
print("-> fg_attempts.csv (%d rows)" % len(fg))
