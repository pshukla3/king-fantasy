import json, re
import nflreadpy as nfl

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

d = nfl.load_depth_charts([2026]).to_pandas()
latest = d["dt"].max()
cur = d[d["dt"] == latest].copy()
print("depth chart snapshot: %s" % latest)

OFF = {"QB": "QB", "RB": "RB", "FB": "RB", "TE": "TE",
       "K": "K", "WR": "WR", "LWR": "WR", "RWR": "WR",
       "SWR": "WR"}
cur = cur[cur["pos_abb"].isin(OFF)]
cur["pos"] = cur["pos_abb"].map(OFF)
cur["pos_rank"] = cur["pos_rank"].fillna(99).astype(int)

DEPTH, BYTEAM = {}, {}
for (tm, pos), g in cur.groupby(["team", "pos"]):
    g = g.sort_values("pos_rank")
    seen = []
    for _, r in g.iterrows():
        k = norm(r["player_name"])
        if k in [x[0] for x in seen]:
            continue
        seen.append((k, r["player_name"], int(r["pos_rank"]),
                     r.get("gsis_id")))
    BYTEAM.setdefault(tm, {})[pos] = [
        {"n": x[1], "rank": i + 1, "gsis": x[3]}
        for i, x in enumerate(seen)]
    for i, x in enumerate(seen):
        DEPTH[x[0]] = {"n": x[1], "tm": tm, "pos": pos,
                       "rank": i + 1, "gsis": x[3],
                       "starter": 1 if i == 0 else 0}

json.dump({"dt": str(latest), "players": DEPTH,
           "teams": BYTEAM},
          open("depth.json", "w"), separators=(",", ":"))
print("depth for %d players across %d teams"
      % (len(DEPTH), len(BYTEAM)))

for pos in ("QB", "RB", "WR", "TE", "K"):
    n = sum(1 for v in DEPTH.values()
            if v["pos"] == pos and v["starter"])
    print("  %-3s starters identified: %d" % (pos, n))

print("\n=== the QBs our old method got wrong ===")
for k in ("caleb williams", "lamar jackson", "baker mayfield",
          "tyler huntley", "tyson bagent", "case keenum"):
    v = DEPTH.get(k)
    if v:
        print("  %-22s %-4s %s%d  %s"
              % (v["n"][:22], v["tm"], v["pos"], v["rank"],
                 "STARTER" if v["starter"] else "backup"))

print("\n=== LA kicker after the Mevis release ===")
for x in BYTEAM.get("LA", {}).get("K", []):
    print("  K%d  %s" % (x["rank"], x["n"]))
