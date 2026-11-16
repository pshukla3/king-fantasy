import json, re, shutil

def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

CAL = json.load(open("calibration.json"))
P = json.load(open("site/_projweek.json"))
shutil.copy("site/_board.json", "site/_board_pre.json")
B = json.load(open("site/_board.json"))

n = 0
moves = []
for r in B.get("rows", []):
    k = norm(r.get("n"))
    v = P.get(k)
    if not v or not v.get("season"):
        continue
    c = CAL.get(v["pos"])
    if not c:
        continue
    new = max(0.0, c["slope"] * v["season"] + c["intercept"])
    old = r.get("live")
    r["live_old"] = old
    r["live"] = round(new, 2)
    r["bye"] = v.get("bye") or r.get("bye")
    n += 1
    if old:
        moves.append((new - old, r["n"], r.get("pos"),
                      old, new))
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("updated %d players (backup: site/_board_pre.json)" % n)

moves.sort(key=lambda x: -abs(x[0]))
print("\n=== biggest movers ===")
print("  %-24s %-4s %7s %7s %7s"
      % ("PLAYER", "POS", "OLD", "NEW", "DIFF"))
for d, nm, pos, o, nw in moves[:20]:
    print("  %-24s %-4s %7.1f %7.1f %+7.1f"
          % (nm[:24], pos, o, nw, d))

print("\n=== new top 20 ===")
rows = [r for r in B["rows"] if r.get("live")]
rows.sort(key=lambda r: -r["live"])
for r in rows[:20]:
    print("  %-24s %-4s %6.1f  (was %s)"
          % (r["n"][:24], r.get("pos"), r["live"],
             r.get("live_old")))
