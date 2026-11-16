import json
import ssl
import urllib.request
import certifi
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
LG = "1312181058833240064"

def get(u):
    r = urllib.request.Request(
        u, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(r, context=CTX,
                                timeout=40) as f:
        return json.load(f)

P = json.load(open("proj_by_sleeper_id.json"))
PJ = json.load(open("sleeper_players.json"))
R = get("https://api.sleeper.app/v1/league/%s/rosters" % LG)

rows = []
for r in R:
    for pid in (r.get("players") or []):
        s = str(pid)
        d = PJ.get(s) or {}
        ps = d.get("position")
        if not ps:
            ps = "DEF" if len(s) <= 3 and s.isalpha() else "?"
        rows.append({"rid": int(r["roster_id"]), "sid": s,
                     "nm": d.get("full_name") or s,
                     "ps": ps,
                     "tm": d.get("team") or "",
                     "ok": s in P})
L = pd.DataFrame(rows)
n = int((~L["ok"]).sum())
print("rostered %d | mapped %d | MISSING %d"
      % (len(L), int(L["ok"].sum()), n))

print("\n=== MISSING BY POSITION ===")
m = L[~L["ok"]]
if len(m):
    print(m.groupby("ps").size().to_string())
    print("\n=== EVERY MISSING PLAYER ===")
    for _, x in m.sort_values(["ps", "nm"]).iterrows():
        print("  rid%-3d %-4s %-26s %s"
              % (x["rid"], x["ps"], str(x["nm"])[:26], x["tm"]))
else:
    print("  none")

B = pd.read_csv("board_final.csv", low_memory=False)
print("\n=== BOARD INVENTORY ===")
print(B.groupby("position").size().to_string())
print("\n  K on board   %d of 32 needed"
      % len(B[B["position"] == "K"]))
print("  DST on board %d of 32 needed"
      % len(B[B["position"].isin(["DST", "DEF"])]))
print("  teams with a DST row: %s"
      % sorted(set(B[B["position"].isin(["DST", "DEF"])]
                   ["team"].astype(str))))

print("\n=== LEAGUE SCORING KEYS ===")
SC = pd.read_csv("league_scoring.csv")
for _, r in SC.iterrows():
    print("  %-24s %s" % (r["key"], r["value"]))

import nflreadpy as nfl

def pl(x):
    return x.to_pandas() if hasattr(x, "to_pandas") else x

W = pl(nfl.load_player_stats(seasons=[2024, 2025]))
dc = [c for c in W.columns
      if c.startswith("def_") or c.startswith("special")
      or "fumble_rec" in c or "safet" in c]
print("\n=== DEFENSIVE STAT COLUMNS AVAILABLE ===")
for c in dc:
    print("  %s" % c)

S = pl(nfl.load_schedules(seasons=[2024, 2025]))
d = S[S["home_score"].notna()]
print("\n=== POINTS ALLOWED SOURCE ===")
print("  completed games with scores: %d" % len(d))
tm = sorted(set(d["home_team"].astype(str))
            | set(d["away_team"].astype(str)))
print("  distinct teams: %d" % len(tm))
print("  %s" % tm)

K = pl(nfl.load_player_stats(seasons=[2025]))
K = K[K["position"] == "K"] if "position" in K.columns else K
kc = [c for c in K.columns
      if "fg" in c.lower() or "pat" in c.lower()
      or "kick" in c.lower()]
print("\n=== KICKER STAT COLUMNS ===")
print("  %s" % kc)
print("  distinct kickers 2025: %d"
      % K["player_id"].nunique())
