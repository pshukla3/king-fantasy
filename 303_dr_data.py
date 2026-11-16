import json
import pandas as pd

C = json.load(open("player_cards.json"))
B = pd.read_csv("board_final.csv")
B = B[B["player_display_name"].notna()]
MR = {}
for _, r in B.iterrows():
    try:
        MR[str(r["player_id"])] = int(r["market_rank"])
    except Exception:
        pass

OUT = []
for k, v in C.items():
    p = v.get("p26") or {}
    gm = p.get("gm") or 17
    pid = str(v.get("id", k))
    adp = v.get("adp")
    rk = v.get("rk")
    OUT.append({
        "i": pid, "n": v.get("nm", ""), "p": v.get("ps", ""),
        "t": v.get("tm", ""), "by": v.get("by"),
        "hs": v.get("hs", ""),
        "rk": int(rk) if rk else 999,
        "prk": v.get("prk"),
        "adp": float(adp) if adp else None,
        "pts": round(float(v.get("szn") or 0), 1),
        "avg": round(float(v.get("ppg") or 0), 1),
        "car": p.get("car", 0), "ryd": p.get("ryd", 0),
        "rtd": p.get("rtd", 0), "tar": p.get("tar", 0),
        "rec": p.get("rec", 0), "cyd": p.get("cyd", 0),
        "ctd": p.get("ctd", 0), "patt": p.get("att", 0),
        "pyd": p.get("pyd", 0), "ptd": p.get("ptd", 0),
        "gm": gm, "st": v.get("st", "")})

OUT = [o for o in OUT if o["n"]]
OUT.sort(key=lambda x: x["rk"])
for i, o in enumerate(OUT):
    o["edge"] = (round(o["adp"] - o["rk"], 1)
                 if o["adp"] else None)
json.dump(OUT, open("site/_dr.json", "w"))

print("wrote site/_dr.json: %d players" % len(OUT))
print("  headshots %d | with adp %d | with p26 carries %d"
      % (sum(1 for o in OUT if o["hs"]),
         sum(1 for o in OUT if o["adp"]),
         sum(1 for o in OUT if o["car"] or o["tar"]
             or o["patt"])))
print("\n  biggest values (adp minus model rank):")
v = [o for o in OUT if o["edge"] is not None]
for o in sorted(v, key=lambda x: -x["edge"])[:6]:
    print("    %-20s %-3s rk%3d adp%6.1f  +%.0f"
          % (o["n"][:20], o["p"], o["rk"], o["adp"],
             o["edge"]))
print("\n  biggest reaches:")
for o in sorted(v, key=lambda x: x["edge"])[:4]:
    print("    %-20s %-3s rk%3d adp%6.1f  %.0f"
          % (o["n"][:20], o["p"], o["rk"], o["adp"],
             o["edge"]))
