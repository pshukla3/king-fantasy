import json, re, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())

# Typical NFL return-to-play windows, in weeks missed.
# Published ranges, not promises -- individuals vary and
# these are the midpoint of what teams actually report.
# 99 = out for the season.
TIMELINE = [
    (r"acl",                      99, "ACL reconstruction, 9-12 months"),
    (r"achilles",                 99, "Achilles rupture, 9-12 months"),
    (r"patell",                   99, "patellar tendon, season"),
    (r"lisfranc",                 99, "Lisfranc, 4-6 months"),
    (r"quad(ricep)?s? tear",      99, "quad tear, season"),
    (r"pectoral|biceps tear",     99, "tendon tear, season"),
    (r"cervical|fusion",          99, "cervical, indefinite"),
    (r"tibia|fibula|femur",       14, "long-bone fracture"),
    (r"jones|5th metatar",        10, "Jones fracture, 8-12 wks"),
    (r"clavicle|collarbone",       7, "clavicle, 6-8 wks"),
    (r"labrum|rotator",            9, "shoulder surgery"),
    (r"meniscus",                  5, "meniscus trim 3-6 wks"),
    (r"mcl",                       4, "MCL sprain, 2-6 wks"),
    (r"pcl",                       6, "PCL sprain"),
    (r"high ankle|syndesmo",       5, "high ankle, 4-6 wks"),
    (r"turf toe",                  4, "turf toe, 2-8 wks"),
    (r"foot",                      4, "foot injury"),
    (r"hamstring",                 2, "hamstring strain, 1-3 wks"),
    (r"groin|adductor",            3, "groin strain, 2-4 wks"),
    (r"calf",                      3, "calf strain, 2-4 wks"),
    (r"quad",                      3, "quad strain, 2-4 wks"),
    (r"ankle",                     2, "ankle sprain, 1-3 wks"),
    (r"knee",                      3, "knee sprain, 2-4 wks"),
    (r"shoulder|ac joint",         2, "shoulder sprain, 1-4 wks"),
    (r"rib",                       3, "rib injury, 2-4 wks"),
    (r"concussion|head",           1, "concussion protocol"),
    (r"hand|thumb|finger|wrist",   3, "hand/wrist, 2-6 wks"),
    (r"back|neck|stinger",         2, "back/neck, 1-3 wks"),
    (r"hip",                       2, "hip, 1-3 wks"),
    (r"illness|personal",          1, "short-term absence"),
]
SEVERE = re.compile(r"torn|tear|rupture|fracture", re.I)

def weeks_out(status, body, notes):
    txt = ("%s %s" % (body or "", notes or "")).lower()
    base, why = None, ""
    for pat, wk, lbl in TIMELINE:
        if re.search(pat, txt):
            base, why = wk, lbl
            break
    if base is None:
        base = {"IR": 5, "PUP": 5, "NA": 4, "Sus": 4,
                "Out": 1, "Doubtful": 1,
                "Questionable": 0}.get(status, 0)
        why = "from designation only"
    # surgery or a tear on a soft-tissue injury pushes it
    if base < 99 and SEVERE.search(txt):
        base = max(base, 6)
        why += " + surgery/tear"
    # NFL rule: a player placed on IR must miss 4 games.
    if status in ("IR", "PUP") and base < 4:
        base = 4
        why += " (IR 4-game minimum)"
    # Questionable means ACTIVE this week. Any tear in the
    # body field is last season's history on a stale record.
    if status in ("Questionable", "Active", "DNR"):
        return 0, "expected to play"
    return base, why

print("pulling Sleeper player file")
ALL = json.loads(U.urlopen(U.Request(
    "https://api.sleeper.app/v1/players/nfl",
    headers={"User-Agent": "Mozilla/5.0"}),
    timeout=60, context=CTX).read())

def norm(s):
    s = str(s or "").lower(); s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

OUT = {}
for pid, p in ALL.items():
    if not isinstance(p, dict):
        continue
    st = p.get("injury_status")
    nm = p.get("full_name")
    if not st or not nm or st == "Active":
        continue
    if p.get("position") not in ("QB", "RB", "WR", "TE", "K"):
        continue
    if not p.get("team"):
        continue
    w, why = weeks_out(st, p.get("injury_body_part"),
                       p.get("injury_notes"))
    if w <= 0:
        continue
    OUT[norm(nm)] = {
        "n": nm, "tm": p.get("team"), "pos": p.get("position"),
        "st": st, "body": p.get("injury_body_part") or "",
        "notes": p.get("injury_notes") or "",
        "weeks": w, "why": why,
    }
json.dump(OUT, open("site/_injtime.json", "w"),
          separators=(",", ":"))
print("timelines for %d players -> site/_injtime.json"
      % len(OUT))

sea = {k: v for k, v in OUT.items() if v["weeks"] >= 99}
print("\n=== OUT FOR THE SEASON (%d) ===" % len(sea))
for v in sorted(sea.values(), key=lambda x: x["n"])[:25]:
    print("  %-22s %-4s %-4s %-14s %-18s %s"
          % (v["n"][:22], v["pos"], v["tm"], v["st"],
             v["body"][:18], v["why"]))

print("\n=== MULTI-WEEK ABSENCES ===")
mid = [v for v in OUT.values() if 2 <= v["weeks"] < 99]
for v in sorted(mid, key=lambda x: -x["weeks"])[:20]:
    print("  %-22s %-4s %-4s %2d wks  %-16s %s"
          % (v["n"][:22], v["pos"], v["tm"], v["weeks"],
             v["body"][:16], v["why"]))

print("\n=== ONE WEEK ONLY ===")
one = [v for v in OUT.values() if v["weeks"] == 1]
for v in sorted(one, key=lambda x: x["n"])[:12]:
    print("  %-22s %-4s %-4s %-14s %s"
          % (v["n"][:22], v["pos"], v["tm"], v["st"],
             v["body"][:20]))
print("  (%d total)" % len(one))
