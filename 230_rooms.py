import pandas as pd
import json
import re
import urllib.request
import ssl
import certifi

def key(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

P = "sleeper_players.json"
PJ = json.load(open(P))
has = any(("depth_chart_order" in v)
          for v in list(PJ.values())[:200])
if not has:
    print("refetching Sleeper for depth charts...")
    ctx = ssl.create_default_context(
        cafile=certifi.where())
    r = urllib.request.urlopen(
        "https://api.sleeper.app/v1/players/nfl",
        timeout=60, context=ctx)
    PJ = json.loads(r.read().decode())
    json.dump(PJ, open(P, "w"))
    print("  saved %d players" % len(PJ))

DC = {}
for d in PJ.values():
    nm, ps = d.get("full_name"), d.get("position")
    if not nm or not ps:
        continue
    DC[(key(nm), ps)] = {
        "tm": d.get("team"),
        "ord": d.get("depth_chart_order"),
        "pos": d.get("depth_chart_position")}
print("depth-chart entries: %d" % len(DC))

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")
B["k"] = B["player_display_name"].apply(key)
S = pd.read_csv("pos_season_panel.csv", low_memory=False)
S = S[S["season"] == 2025]
A25 = dict(zip(S["player_id"].astype(str), S["ppg"]))

def room(tm):
    d = B[(B["team"] == tm)
          & (B["position"].isin(["WR", "TE", "RB"]))]
    d = d[d["pp"].fillna(0) > 0]
    return d.sort_values("pp", ascending=False)

for tm in ["TEN", "MIN", "CIN"]:
    print("\n=== %s SKILL ROOM ===" % tm)
    print("  %-22s %-3s %6s %6s %5s %7s"
          % ("player", "pos", "2025", "2026", "dpth", "rank"))
    print("  " + "-" * 56)
    for _, r in room(tm).head(8).iterrows():
        e = DC.get((r["k"], str(r["position"])), {})
        a = A25.get(str(r["player_id"]))
        o = e.get("ord")
        print("  %-22s %-3s %6s %6.2f %5s %7d"
              % (str(r["player_display_name"])[:22],
                 r["position"],
                 "--" if a is None or a != a
                 else "%.1f" % a,
                 r["pp"],
                 "--" if o is None else "%.0f" % o,
                 int(r["rank"])))

print("\n" + "=" * 58)
print("=== THE THREE YOU FLAGGED ===")
NM = ["Wan'Dale Robinson", "Carnell Tate",
      "Justin Jefferson", "Ja'Marr Chase",
      "Puka Nacua", "Jaxon Smith-Njigba"]
V = pd.read_csv("proj_2026.csv")
try:
    RK = pd.read_csv("rookie_proj_2026.csv")
except IOError:
    RK = pd.DataFrame()
print("  %-22s %-4s %6s %6s %6s %5s %6s"
      % ("player", "tm", "2025", "PROJ", "moved",
         "dpth", "ovr"))
print("  " + "-" * 62)
for nm in NM:
    h = B[B["player_display_name"].astype(str)
          .str.contains(nm, na=False, regex=False)]
    if not len(h):
        print("  %-22s not on board" % nm[:22])
        continue
    r = h.sort_values("rank").iloc[0]
    e = DC.get((key(nm), str(r["position"])), {})
    v = V[V["player_display_name"].astype(str)
          .str.contains(nm, na=False, regex=False)]
    mv = "--"
    a = "--"
    if len(v):
        mv = "yes" if bool(v.iloc[0]["moved"]) else "no"
        a = "%.1f" % v.iloc[0]["ppg25"]
    elif len(RK):
        q = RK[RK["nm"].astype(str)
               .str.contains(nm, na=False, regex=False)]
        if len(q):
            mv = "ROOK"
    o = e.get("ord")
    print("  %-22s %-4s %6s %6.2f %6s %5s %6d"
          % (nm[:22], str(r["team"])[:4], a, r["pp"], mv,
             "--" if o is None else "%.0f" % o,
             int(r["rank"])))

print("\n  dpth = Sleeper depth-chart order, 1 = starter")
print("  a WR2 label from Sleeper is not gospel in August,")
print("  but it is the only depth signal we have that is")
print("  independent of last year's box score.")
