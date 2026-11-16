import json
import re
import ssl
import urllib.request
import certifi
import pandas as pd

def get(u):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(u, context=ctx,
                                timeout=180) as r:
        return json.load(r)

def key(s):
    return re.sub(r"[^a-z]", "", str(s).lower())

print("fetching fresh Sleeper player map...")
PJ = get("https://api.sleeper.app/v1/players/nfl")
json.dump(PJ, open("sleeper_players_fresh.json", "w"))
print("  players returned: %d" % len(PJ))

k0 = list(PJ.keys())[0]
print("  record keys: %s" % sorted(PJ[k0].keys()))

FLDS = ["full_name", "position", "team", "status",
        "active", "years_exp", "injury_status"]
print("\n=== SPOT CHECK ===")
for who in ["thielen", "kelce", "nacua", "diggs",
            "gronkowski"]:
    hit = [d for d in PJ.values()
           if who in str(d.get("full_name", "")).lower()]
    for d in hit[:2]:
        print("  %s" % json.dumps(
            {f: d.get(f) for f in FLDS}))

print("\n=== STATUS VALUES IN THE FEED ===")
st = {}
for d in PJ.values():
    st[str(d.get("status"))] = st.get(
        str(d.get("status")), 0) + 1
for k, v in sorted(st.items(), key=lambda x: -x[1])[:12]:
    print("  %-28s %6d" % (k, v))

IDX = {}
for sid, d in PJ.items():
    nm, ps = d.get("full_name"), d.get("position")
    if not nm or not ps:
        continue
    IDX.setdefault((key(nm), str(ps)), d)

B = pd.read_csv("board_final.csv", low_memory=False)
B["pp"] = pd.to_numeric(B["points"], errors="coerce")

rows = []
for _, r in B.iterrows():
    ps = str(r["position"])
    if ps in ("DST", "DEF"):
        continue
    d = IDX.get((key(r["player_display_name"]), ps))
    if d is None:
        flag = "NOT IN FEED"
        tm, stt, act = "", "", ""
    else:
        tm = d.get("team")
        stt = str(d.get("status"))
        act = d.get("active")
        if not tm:
            flag = "NO TEAM"
        elif act is False:
            flag = "INACTIVE"
        elif stt in ("Retired",):
            flag = "RETIRED"
        else:
            flag = ""
    rows.append({"pid": r["player_id"],
                 "nm": r["player_display_name"],
                 "ps": ps, "ours": str(r["team"]),
                 "live": tm or "", "status": stt,
                 "ppg": r["pp"], "rank": r.get("rank"),
                 "flag": flag})

A = pd.DataFrame(rows)
A.to_csv("roster_audit.csv", index=False)
bad = A[A["flag"] != ""]
print("\n=== BOARD AUDIT ===")
print("  skill rows checked : %d" % len(A))
print("  flagged            : %d" % len(bad))
print(bad.groupby("flag").size().to_string())

print("\n=== FLAGGED PLAYERS WITH A REAL PROJECTION ===")
h = bad[bad["ppg"].fillna(0) > 3].sort_values(
    "ppg", ascending=False)
print("  %-24s %-4s %-5s %-6s %-14s %6s"
      % ("player", "pos", "ours", "live", "flag", "ppg"))
print("  " + "-" * 66)
for _, r in h.iterrows():
    print("  %-24s %-4s %-5s %-6s %-14s %6.2f"
          % (str(r["nm"])[:24], r["ps"], r["ours"],
             r["live"] or "--", r["flag"], r["ppg"]))
print("\n  total projected points sitting on dead rows: %.0f"
      % h["ppg"].sum())

print("\n" + "=" * 62)
print("=== TEAM MISMATCHES, ALL 32 ===")
FIX = {"AZ": "ARI", "LAR": "LA", "WSH": "WAS",
       "JAC": "JAX"}
A["live2"] = A["live"].replace(FIX)
A["ours2"] = A["ours"].replace(FIX)
M = A[(A["flag"] == "") & (A["live2"] != "")
      & (A["ours2"] != A["live2"])]
print("  rows where our team != live team: %d" % len(M))
if len(M):
    print("\n  %-24s %-4s %-6s %-6s %6s"
          % ("player", "pos", "ours", "live", "ppg"))
    print("  " + "-" * 52)
    for _, r in M.sort_values(
            "ppg", ascending=False).head(40).iterrows():
        print("  %-24s %-4s %-6s %-6s %6s"
              % (str(r["nm"])[:24], r["ps"], r["ours2"],
                 r["live2"],
                 "--" if r["ppg"] != r["ppg"]
                 else "%.2f" % r["ppg"]))

print("\n=== ROSTER COUNT BY LIVE TEAM ===")
ok = A[(A["flag"] == "") & (A["live2"] != "")]
c = ok.groupby(["live2", "ps"]).size().unstack(
    fill_value=0)
for col in ["QB", "RB", "WR", "TE", "K"]:
    if col not in c.columns:
        c[col] = 0
c = c[["QB", "RB", "WR", "TE", "K"]]
c["TOT"] = c.sum(axis=1)
print(c.sort_index().to_string())
print("\n  teams represented: %d of 32" % len(c))
print("  a team with 0 QBs or 0 Ks means our board")
print("  is missing that room entirely")
