import json
import ssl
import urllib.request
import pandas as pd

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl.create_default_context()

import sys
_env = None
USERNAME = (sys.argv[1] if len(sys.argv) > 1
            else input("Sleeper username: ").strip())
SEASON = "2026"
BASE = "https://api.sleeper.app/v1"
UA = {"User-Agent": "accuracy.report/1.0"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=UA)
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))

u = get("/user/%s" % USERNAME)
if not u:
    raise SystemExit(
        "Sleeper has no user %r.\n"
        "  use your USERNAME (the @handle), not display name\n"
        "  find it in the Sleeper app under Account"
        % USERNAME)
print("user: %s  id %s" % (u["display_name"], u["user_id"]))

LG = get("/user/%s/leagues/nfl/%s" % (u["user_id"], SEASON))
print("leagues found: %d" % len(LG))
for i, l in enumerate(LG):
    print("  [%d] %-28s %2d teams  %s"
          % (i, l["name"][:28], l["total_rosters"], l["league_id"]))

if not LG:
    raise SystemExit("no leagues for that username in %s" % SEASON)

L = LG[0]
print("\nusing: %s" % L["name"])
print("roster slots: %s" % L["roster_positions"])
json.dump(L, open("sleeper_league.json", "w"), indent=1)
print("saved sleeper_league.json")

SC = L["scoring_settings"]
print("\n=== YOUR ACTUAL SCORING SETTINGS (%d keys) ===" % len(SC))

GROUPS = [
    ("PASSING",  ["pass_yd", "pass_td", "pass_int", "pass_2pt"]),
    ("RUSHING",  ["rush_yd", "rush_td", "rush_2pt"]),
    ("RECEIVING", ["rec", "rec_yd", "rec_td", "rec_2pt"]),
    ("FUMBLES",  ["fum", "fum_lost", "fum_rec_td"]),
    ("KICKING",  ["fgm", "fgmiss", "xpm", "xpmiss",
                  "fgm_0_19", "fgm_20_29", "fgm_30_39",
                  "fgm_40_49", "fgm_50p",
                  "fgmiss_0_19", "fgmiss_20_29",
                  "fgmiss_30_39", "fgmiss_40_49", "fgmiss_50p"]),
    ("DEFENSE",  ["sack", "int", "fum_rec", "safe", "def_td",
                  "blk_kick", "def_st_td", "st_td", "st_ff",
                  "pts_allow_0", "pts_allow_1_6", "pts_allow_7_13",
                  "pts_allow_14_20", "pts_allow_21_27",
                  "pts_allow_28_34", "pts_allow_35p",
                  "yds_allow_0_100", "yds_allow_100_199",
                  "yds_allow_200_299", "yds_allow_300_349",
                  "yds_allow_350_399", "yds_allow_400_449",
                  "yds_allow_450_499", "yds_allow_500_549",
                  "yds_allow_550p"]),
]
seen = set()
for lbl, keys in GROUPS:
    hit = [(k, SC[k]) for k in keys if k in SC]
    seen.update(k for k, _ in hit)
    if not hit:
        continue
    print("\n  %s" % lbl)
    for k, v in hit:
        print("    %-20s %+g" % (k, v))

rest = sorted(set(SC) - seen)
if rest:
    print("\n  OTHER (%d)" % len(rest))
    for k in rest:
        print("    %-20s %+g" % (k, SC[k]))

pd.DataFrame(sorted(SC.items()),
             columns=["key", "value"]).to_csv(
    "league_scoring.csv", index=False)
print("\nsaved league_scoring.csv")

LID = L["league_id"]
R = get("/league/%s/rosters" % LID)
US = get("/league/%s/users" % LID)
NAME = {x["user_id"]: (x.get("metadata") or {}).get("team_name")
        or x["display_name"] for x in US}

print("\npulling player map (~5MB, once per day max) ...")
P = get("/players/nfl")
print("players: %d" % len(P))
json.dump({k: {"n": v.get("full_name") or k,
               "p": v.get("position"),
               "t": v.get("team")}
           for k, v in P.items()},
          open("sleeper_players.json", "w"))

mine = [x for x in R if x["owner_id"] == u["user_id"]]
if not mine:
    print("no roster owned by you in this league")
else:
    r0 = mine[0]
    st = set(r0.get("starters") or [])
    rows = []
    for pid in (r0.get("players") or []):
        d = P.get(pid, {})
        rows.append({
            "player": d.get("full_name") or pid,
            "pos": d.get("position") or
                   ("DEF" if pid.isalpha() else "?"),
            "team": d.get("team") or pid,
            "slot": "START" if pid in st else "BENCH",
            "sleeper_id": pid})
    M = pd.DataFrame(rows).sort_values(["slot", "pos", "player"])
    M.to_csv("my_roster_sleeper.csv", index=False)
    print("\n=== YOUR ROSTER (%s) ===" % NAME.get(u["user_id"], "you"))
    print(M.to_string(index=False))
    print("\nsaved my_roster_sleeper.csv")

print("\nleague teams:")
for x in R:
    print("  roster %-2d  %s" % (x["roster_id"],
                                 NAME.get(x["owner_id"], "orphan")))
