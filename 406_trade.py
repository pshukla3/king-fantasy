import json, re
import pandas as pd

GIVE = ["Deebo Samuel"]
GET = ["Juwan Johnson", "A.J. Brown"]

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"\s+(jr|sr|ii|iii|iv)\.?$", "", s)
    s = re.sub(r"[.'`\u2019\-]", "", s)
    return re.sub(r"\s+", " ", s).strip()

B = pd.read_csv("board_final.csv")
B["k"] = B["player_display_name"].map(norm)
INJ = json.load(open("site/_inj.json"))
try:
    REA = json.load(open("site/_reasons.json"))
except IOError:
    REA = {}

def row(nm):
    z = B[B["k"] == norm(nm)]
    if not len(z):
        z = B[B["player_display_name"].str.contains(
            nm.split()[-1], na=False)]
    return z.iloc[0] if len(z) else None

def show(nm, side):
    r = row(nm)
    if r is None:
        print("  %-22s NOT FOUND" % nm)
        return 0.0
    j = INJ.get(norm(nm)) or {}
    val = float(r.get("val100") or 0)
    print("  %-22s #%-4d %-4s%-3s  value %-5.0f %s"
          % (r["player_display_name"][:22],
             int(r["rank_v"]), r["position"],
             "", val,
             ("[" + str(j.get("status")) + " - "
              + str(j.get("type")) + "]")
             if j.get("status") not in (None, "Active")
             else ""))
    d = REA.get(norm(nm))
    if d and d.get("line"):
        print("      " + d["line"][:120])
    return val

print("=== YOU GIVE ===")
g = sum(show(n, "give") for n in GIVE)
print("\n=== YOU GET ===")
t = sum(show(n, "get") for n in GET)
print("\ngive %.0f  |  get %.0f  |  net %+.0f" % (g, t, t - g))

print("\n=== YOUR STARTING LINEUP IMPACT ===")
D = json.load(open("site/_slteams.json"))
me = next((x for x in D["teams"]
           if str(x.get("owner", "")).startswith("Shukie")),
          D["teams"][0])
have = {norm(p["n"]) for p in me["players"]}
print("  on your roster now: %s"
      % ", ".join(n for n in GIVE if norm(n) in have))
wr = sorted([p for p in me["players"] if p["pos"] == "WR"],
            key=lambda x: -x["ppg"])[:5]
te = sorted([p for p in me["players"] if p["pos"] == "TE"],
            key=lambda x: -x["ppg"])[:3]
print("  your WRs :", ", ".join(
    "%s %.1f" % (p["n"].split()[-1], p["ppg"]) for p in wr))
print("  your TEs :", ", ".join(
    "%s %.1f" % (p["n"].split()[-1], p["ppg"]) for p in te))
