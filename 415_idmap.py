import json, os
import nflreadpy as nfl

POS = {"QB", "RB", "WR", "TE", "K", "DEF", "DST", "PK"}

d = nfl.load_ff_playerids()
try:
    d = d.to_pandas()
except Exception:
    pass
print("crosswalk rows: %d" % len(d))

d = d[d["position"].isin(POS)].copy()
print("fantasy positions: %d" % len(d))

def sid(v):
    if v is None or v != v:
        return None
    s = str(v)
    return s[:-2] if s.endswith(".0") else s

ESPN, YAHOO, NAME = {}, {}, {}
for _, r in d.iterrows():
    sl = sid(r.get("gsis_id"))
    if not sl:
        continue
    e = sid(r.get("espn_id"))
    y = sid(r.get("yahoo_id"))
    if e:
        ESPN[e] = sl
    if y:
        YAHOO[y] = sl
    mn = r.get("merge_name")
    if isinstance(mn, str) and mn:
        NAME[mn] = sl

print("  espn -> gsis : %d" % len(ESPN))
print("  yahoo -> gsis: %d" % len(YAHOO))
print("  name -> gsis  : %d" % len(NAME))

OUT = {"espn": ESPN, "yahoo": YAHOO, "name": NAME}
os.makedirs("site", exist_ok=True)
json.dump(OUT, open("site/_idmap.json", "w"),
          separators=(",", ":"))
print("wrote site/_idmap.json (%d KB)"
      % (os.path.getsize("site/_idmap.json") // 1024))

# The metric that matters: coverage of OUR projected
# players, not of the crosswalk as a whole.
print("\n=== coverage against our board ===")
if not os.path.exists("site/_board.json"):
    print("  site/_board.json missing -- run 368_board.py")
else:
    B = json.load(open("site/_board.json"))
    rows = B if isinstance(B, list) else (
        B.get("rows") or B.get("players") or [])
    print("  board rows: %d" % len(rows))
    if rows:
        print("  board keys: %s" % list(rows[0].keys())[:14])
    idf = None
    for c in ("player_id", "sleeper_id", "pid", "k", "id"):
        if rows and c in rows[0]:
            idf = c
            break
    print("  id field: %s" % idf)
    if idf:
        rev = set(ESPN.values())
        ryh = set(YAHOO.values())
        tot = hit_e = hit_y = dst = 0
        miss = []
        for r in rows:
            p = str(r.get(idf) or "")
            ps = str(r.get("position") or r.get("pos") or "")
            if ps in ("DEF", "DST"):
                dst += 1
                continue
            if not p:
                continue
            tot += 1
            if p in rev:
                hit_e += 1
            else:
                miss.append(r.get("name") or r.get("player")
                            or p)
            if p in ryh:
                hit_y += 1
        f = lambda a, b: (100.0 * a / b) if b else 0.0
        print("  skill players: %d  (DST handled "
              "separately: %d)" % (tot, dst))
        print("  mappable to ESPN : %d (%.1f%%)"
              % (hit_e, f(hit_e, tot)))
        print("  mappable to Yahoo: %d (%.1f%%)"
              % (hit_y, f(hit_y, tot)))
        print("  first 15 ESPN misses: %s"
              % ", ".join(str(m) for m in miss[:15]))
