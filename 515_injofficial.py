import json, re, datetime
import nflreadpy as nfl

# measured on 2,498 injury-report rows vs snap counts
PP = json.load(open("playprob.json"))
PS = {"Full Participation in Practice": "Full",
      "Limited Participation in Practice": "Limited",
      "Did Not Participate In Practice": "DNP"}

def prob(status, practice):
    d = PP.get(status)
    if d is None:
        return 1.0
    return d.get(PS.get(practice, ""), d.get("any", 0.0))

# recovery windows, unchanged from 465 -- published ranges
TIMELINE = [
    (r"acl", 99), (r"achilles", 99), (r"patell", 99),
    (r"lisfranc", 99), (r"pectoral|biceps tear", 99),
    (r"tibia|fibula|femur", 14), (r"jones|5th metatar", 10),
    (r"clavicle|collarbone", 7), (r"labrum|rotator", 9),
    (r"meniscus", 5), (r"mcl", 4), (r"pcl", 6),
    (r"high ankle|syndesmo", 5), (r"turf toe", 4),
    (r"foot", 4), (r"hamstring", 2), (r"groin|adductor", 3),
    (r"calf", 3), (r"quad", 3), (r"ankle", 2), (r"knee", 3),
    (r"shoulder|ac joint", 2), (r"rib", 3),
    (r"concussion|head", 1), (r"hand|thumb|finger|wrist", 3),
    (r"back|neck|stinger", 2), (r"hip", 2),
    (r"illness|personal", 1),
]

def weeks(body):
    t = str(body or "").lower()
    for pat, wk in TIMELINE:
        if re.search(pat, t):
            return wk
    return 1

def norm(s):
    s = re.sub(r"[^a-z ]", "", str(s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

d = nfl.load_injuries([2026]).to_pandas()
d = d[d["position"].isin(["QB", "RB", "WR", "TE", "K"])]
wk = int(d["week"].max())
cur = d[(d["week"] == wk) & d["report_status"].notna()]
print("official injury report, week %d: %d designations"
      % (wk, len(cur)))

OUT = {}
for _, r in cur.iterrows():
    st = r["report_status"]
    pr = r.get("practice_status")
    p = prob(st, pr)
    body = r.get("report_primary_injury")
    w = weeks(body)
    if st == "Out":
        w = max(1, w)
    elif st == "Doubtful":
        w = max(1, min(w, 2))
    else:                      # Questionable
        w = 0 if p >= 0.5 else 1
    OUT[norm(r["full_name"])] = {
        "n": r["full_name"], "tm": r["team"],
        "pos": r["position"], "st": st,
        "body": str(body or ""),
        "practice": PS.get(pr, ""),
        "play_prob": round(float(p), 3),
        "weeks": int(w),
        "why": "official report wk%d" % wk,
    }

# keep anyone Sleeper flags as season-ending that the
# weekly report no longer lists (IR players drop off it)
try:
    old = json.load(open("site/_injtime.json"))
    kept = 0
    for k, v in old.items():
        if v.get("weeks", 0) >= 99 and k not in OUT:
            v["play_prob"] = 0.0
            v["why"] = (v.get("why") or "") + " (season-ending)"
            OUT[k] = v
            kept += 1
    print("carried %d season-ending cases forward" % kept)
except Exception as e:
    print("prior injtime:", e)

json.dump(OUT, open("site/_injtime.json", "w"),
          separators=(",", ":"))
print("wrote site/_injtime.json (%d players)" % len(OUT))

print("\n%-22s %-4s %-13s %-9s %6s %5s"
      % ("PLAYER", "TM", "STATUS", "PRACTICE", "PLAY%", "WKS"))
for v in sorted(OUT.values(),
                key=lambda x: (x["st"] != "Questionable",
                               -x.get("play_prob", 0)))[:18]:
    print("%-22s %-4s %-13s %-9s %5.0f%% %5s"
          % (v["n"][:22], v.get("tm"), v["st"][:13],
             v.get("practice", "")[:9],
             v.get("play_prob", 0) * 100, v["weeks"]))
