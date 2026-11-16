import json, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())

from namekey import nk as norm

print("pulling Sleeper player file")
ALL = json.loads(U.urlopen(U.Request(
    "https://api.sleeper.app/v1/players/nfl",
    headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60, context=CTX).read())

POS = {"QB", "RB", "WR", "TE", "K", "DEF"}
pool = []
for pid, p in ALL.items():
    if not isinstance(p, dict):
        continue
    pos = p.get("position")
    if pos not in POS:
        continue
    if pos != "DEF" and not p.get("team"):
        continue
    sr = p.get("search_rank")
    if sr is None or sr >= 9999:
        continue
    nm = p.get("full_name") or p.get("last_name") or ""
    if not nm:
        continue
    pool.append((sr, norm(nm), nm, pos, p.get("team")))

# search_rank is Sleeper's internal ordering across every
# player. Convert it into a DRAFT POSITION on our own
# scale: sort the draftable pool, then number it 1..N.
pool.sort(key=lambda x: x[0])
ADP = {}
for i, (sr, key, nm, pos, tm) in enumerate(pool, 1):
    ADP[key] = {"adp": i, "pos": pos, "tm": tm, "n": nm}
print("draftable pool: %d players" % len(ADP))

B = json.load(open("site/_board.json"))
hit = miss = 0
for r in B["rows"]:
    k = norm(r.get("n"))
    v = ADP.get(k)
    if not v:
        for sf in (" jr", " sr", " ii", " iii", " iv", " v"):
            if ADP.get(k + sf):
                v = ADP[k + sf]
                break
            if k.endswith(sf) and ADP.get(k[:-len(sf)]):
                v = ADP[k[:-len(sf)]]
                break
    if v:
        r["adp"] = float(v["adp"])
        hit += 1
    else:
        r["adp"] = None
        miss += 1
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("ADP set on %d rows, %d had no match" % (hit, miss))

rows = [r for r in B["rows"] if r.get("adp") and r.get("rk")]
rows.sort(key=lambda r: r["adp"])
print("\n=== OUR ADP, TOP 15 ===")
print("  %-5s %-24s %-4s %-4s %6s  %s"
      % ("ADP", "PLAYER", "POS", "TM", "OURRK", "EDGE"))
for r in rows[:15]:
    e = r["adp"] - r["rk"]
    print("  %-5.0f %-24s %-4s %-4s %6d  %+5.0f"
          % (r["adp"], r["n"][:24], r.get("pos"),
             r.get("tm"), r["rk"], e))

print("\n=== BIGGEST DISAGREEMENTS WITH THE MARKET ===")
rows.sort(key=lambda r: -(r["adp"] - r["rk"]))
print("  we like more than the market:")
for r in rows[:8]:
    print("    %-24s %-3s  adp %3.0f -> our rk %3d  (%+.0f)"
          % (r["n"][:24], r.get("pos"), r["adp"], r["rk"],
             r["adp"] - r["rk"]))
print("  we like less:")
for r in rows[-8:][::-1]:
    print("    %-24s %-3s  adp %3.0f -> our rk %3d  (%+.0f)"
          % (r["n"][:24], r.get("pos"), r["adp"], r["rk"],
             r["adp"] - r["rk"]))

k = [r for r in B["rows"] if r.get("pos") == "K"
     and r.get("live")]
k.sort(key=lambda r: -r["live"])
print("\n=== KICKER ADP ON OUR SCALE ===")
for r in k[:8]:
    print("    %-24s adp %s   our rk %s"
          % (r["n"][:24], r.get("adp"), r.get("rk")))
