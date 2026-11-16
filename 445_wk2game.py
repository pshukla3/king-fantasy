import json, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
HD = {"User-Agent": "Mozilla/5.0"}

def get(u):
    return json.loads(U.urlopen(U.Request(u, headers=HD),
                                timeout=30, context=CTX).read())

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

E = ("https://site.api.espn.com/apis/site/v2/sports/"
     "football/nfl/")

print("=== which week-2 games are final? ===")
sb = get(E + "scoreboard?seasontype=2&dates=2026&week=2")
finals = []
for g in sb.get("events", []):
    st = ((g.get("status") or {}).get("type") or {})
    c = (g.get("competitions") or [{}])[0]
    names = []
    for x in c.get("competitors", []):
        names.append("%s %s" % (
            (x.get("team") or {}).get("abbreviation"),
            x.get("score")))
    print("  %-28s %-10s %s"
          % (g.get("shortName"), st.get("state"),
             " - ".join(names)))
    if st.get("state") == "post":
        finals.append(g)
print("  finals: %d" % len(finals))

SET = json.load(open("site/_scoring.json"))
PM = json.load(open("site/_pmap.json"))
PROJ = json.load(open("site/_wkproj.json")).get("2", {})
SKIP = {"pts_ppr", "pts_std", "pts_half_ppr", "gp",
        "gms_active", "tm_def_snp", "tm_off_snp",
        "tm_st_snp"}

def score(st):
    return sum(SET[k] * v for k, v in (st or {}).items()
               if k in SET and SET[k] and k not in SKIP)

ST = get("https://api.sleeper.app/v1/stats/nfl/"
         "regular/2026/2")
print("\n=== players with week-2 stats: %d ===" % len(ST))

rows = []
for pid, s in ST.items():
    if pid.startswith("TEAM_"):
        continue
    m = PM.get(str(pid)) or {}
    nm = m.get("n")
    if not nm:
        continue
    pts = score(s)
    if abs(pts) < 0.01 and not s.get("off_snp"):
        continue
    key = m.get("t") if m.get("p") in ("DEF", "DST") \
        else norm(nm)
    pj = PROJ.get(key)
    rows.append({
        "n": nm, "p": m.get("p"), "t": m.get("t"),
        "act": round(pts, 2), "proj": pj,
        "err": (round(pts - pj, 2) if pj is not None
                else None),
        "snp": s.get("off_snp"), "tgt": s.get("rec_tgt"),
        "rec": s.get("rec"), "car": s.get("rush_att"),
        "ryd": s.get("rush_yd"), "cyd": s.get("rec_yd"),
    })

rows.sort(key=lambda r: -r["act"])
print("\n=== top 20 scorers, vs what we projected ===")
print("  %-22s %-4s %-4s %6s %6s %7s %5s %4s %4s"
      % ("PLAYER", "POS", "TM", "ACT", "PROJ", "ERR",
         "SNAP", "TGT", "CAR"))
for r in rows[:20]:
    print("  %-22s %-4s %-4s %6.2f %6s %7s %5s %4s %4s"
          % (r["n"][:22], r["p"], r["t"], r["act"],
             ("%.1f" % r["proj"]) if r["proj"] else "-",
             ("%+.1f" % r["err"]) if r["err"] is not None
             else "-",
             r["snp"] or "-", r["tgt"] or "-",
             r["car"] or "-"))

scored = [r for r in rows if r["err"] is not None]
if scored:
    import statistics as sx
    mae = sx.mean(abs(r["err"]) for r in scored)
    bias = sx.mean(r["err"] for r in scored)
    print("\n=== accuracy on the games played so far ===")
    print("  players scored: %d" % len(scored))
    print("  MAE  %.2f   bias %+.2f" % (mae, bias))
    print("  (week 1 MAE was 5.15)")
    scored.sort(key=lambda r: -abs(r["err"]))
    print("\n  biggest misses:")
    for r in scored[:10]:
        print("    %-22s %-4s proj %5.1f  actual %6.2f  "
              "%+6.2f  snaps %s"
              % (r["n"][:22], r["p"], r["proj"], r["act"],
                 r["err"], r["snp"] or "-"))

json.dump(rows, open("site/_wk2live.json", "w"),
          separators=(",", ":"))
print("\nwrote site/_wk2live.json (%d rows)" % len(rows))
