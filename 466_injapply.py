import json, re, datetime

_A = datetime.datetime(2026, 9, 8,
                       tzinfo=datetime.timezone.utc)
CUR = max(1, min(18, (datetime.datetime.now(
    datetime.timezone.utc) - _A).days // 7 + 1))
LAST = 17          # fantasy regular season ends wk 17
print("current week %d" % CUR)

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

B = json.load(open("site/_board.json"))
rows = B["rows"]
T = json.load(open("site/_injtime.json"))
# suffix aliases so "Deebo Samuel Sr." matches
for k in list(T):
    for sf in (" sr", " jr", " ii", " iii", " iv", " v"):
        if k.endswith(sf):
            T.setdefault(k[:-len(sf)], T[k])

hit = 0
for r in rows:
    ppg = r.get("live")
    if ppg is None:
        continue
    r["_old_rk"] = r.get("rk")
    # games left this week onward, minus a future bye
    left = max(0, LAST - CUR + 1)
    bye = r.get("bye")
    if bye and bye >= CUR:
        left -= 1
    v = T.get(norm(r.get("n")))
    miss, why = 0, ""
    if v:
        miss = left if v["weeks"] >= 99 else min(v["weeks"], left)
        why = v["why"]
        r["inj"] = v["st"]
        r["inj_body"] = v["body"]
        r["inj_why"] = why
        r["inj_wks"] = ("OUT FOR SEASON" if v["weeks"] >= 99
                        else "%d wk" % v["weeks"])
        hit += 1
    # A "Questionable" player is a coin flip -- measured at
    # 55% over 1,305 cases (63% full practice, 39% DNP).
    # Scale THIS week by that probability; later weeks are
    # unaffected because the designation only covers one game.
    pp = (v or {}).get("play_prob")
    if pp is not None and pp < 1.0 and r.get("wk"):
        for _x in r["wk"]:
            if _x.get("o") != "BYE" and not _x.get("out"):
                _x["m"] = round(_x["m"] * pp, 2)
                _x["play_prob"] = pp
                break
        r["play_prob"] = pp

    gl = max(0, left - miss)
    r["gleft"] = gl
    r["miss"] = miss
    # ppg is UNCHANGED - he scores the same when he plays.
    # what an injury costs you is games, not talent.
    r["ros"] = round(ppg * gl, 1)
    # rank on VALUE OVER REPLACEMENT x games left, not raw
    # points -- a QB at 17 ppg is replaceable, a WR is not
    vp = r.get("vorp")
    r["rosv"] = round((vp if vp is not None else 0.0) * gl, 2)
    if gl == 0:
        # OUT FOR THE SEASON. He cannot score. Zero means
        # zero everywhere, and he sorts below every healthy
        # player -- 0 must not outrank a negative VORP.
        for f in ("live", "base", "ceil", "floor",
                  "vorp", "uvorp", "val", "uval", "ros"):
            if f in r:
                r[f] = 0.0
        r["rosv"] = -1e9
        r["out_season"] = 1

print("applied timelines to %d players" % hit)

live = [r for r in rows if r.get("ros") is not None]
live.sort(key=lambda r: (-(r["rosv"] or 0), -(r["ros"] or 0)))
bypos = {}
for i, r in enumerate(live, 1):
    r["rk"] = i
    p = r.get("pos")
    bypos[p] = bypos.get(p, 0) + 1
    r["posrk"] = bypos[p]
json.dump(B, open("site/_board.json", "w"),
          separators=(",", ":"))
print("re-ranked %d players on rest-of-season total\n" % len(live))

print("=== OUT FOR THE SEASON ===")
for r in live:
    if r.get("miss") and r["gleft"] == 0:
        print("  %-22s %-3s %-4s rk %3d  ppg %5.1f  ROS 0"
              % (r["n"][:22], r.get("pos"), r.get("tm"),
                 r["rk"], r["live"]))

print("\n=== INJURED BUT COMING BACK ===")
tmp = [r for r in live if r.get("miss") and r["gleft"] > 0]
tmp.sort(key=lambda r: -(r["ros"] or 0))
print("  %-22s %-3s %4s %6s %5s %6s  %s"
      % ("PLAYER", "POS", "RK", "PPG", "MISS", "ROS", "WHY"))
for r in tmp[:18]:
    print("  %-22s %-3s %4d %6.1f %5d %6.1f  %s"
          % (r["n"][:22], r.get("pos"), r["rk"], r["live"],
             r["miss"], r["ros"], (r.get("inj_why") or "")[:26]))

mv = [(r["_old_rk"] - r["rk"], r) for r in live if r.get("_old_rk")]
mv.sort(key=lambda x: x[0])
print("\n=== BIGGEST FALLS ===")
for d, r in mv[:12]:
    print("  %-22s %-3s %4s -> %4d  ppg %5.1f  %s"
          % (r["n"][:22], r.get("pos"), r["_old_rk"], r["rk"],
             r["live"], r.get("inj_wks") or ""))
print("\n=== BIGGEST RISES ===")
for d, r in mv[-12:][::-1]:
    print("  %-22s %-3s %4s -> %4d  ppg %5.1f"
          % (r["n"][:22], r.get("pos"), r["_old_rk"],
             r["rk"], r["live"]))
