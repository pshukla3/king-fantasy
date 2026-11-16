import json
import pandas as pd

C = json.load(open("player_cards.json"))
B = pd.read_csv("board_final.csv", low_memory=False)
B["player_id"] = B["player_id"].astype(str)
ADP = dict(zip(B["player_id"],
               pd.to_numeric(B["adp"], errors="coerce")))
RANK = dict(zip(B["player_id"],
                pd.to_numeric(B["rank"], errors="coerce")))
CUR = dict(zip(B["player_id"],
               pd.to_numeric(B["points"], errors="coerce")))

PRESETS = {
    "full_ppr": {"rec": 1.0, "te_rec": 1.0},
    "half_ppr": {"rec": 0.5, "te_rec": 0.5},
    "standard": {"rec": 0.0, "te_rec": 0.0},
    "te_prem":  {"rec": 1.0, "te_rec": 1.5},
}
BASE = {"pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0,
        "rush_yd": 0.1, "rush_td": 6.0,
        "rec_yd": 0.1, "rec_td": 6.0, "fum": -2.0}

def score(p, preset, passtd=4.0):
    d = p.get("p26")
    if not d:
        return None
    s = PRESETS[preset]
    r = s["te_rec"] if p["ps"] == "TE" else s["rec"]
    return (d["pyd"] * BASE["pass_yd"]
            + d["ptd"] * passtd
            + d["int"] * BASE["pass_int"]
            + d["ryd"] * BASE["rush_yd"]
            + d["rtd"] * BASE["rush_td"]
            + d["rec"] * r
            + d["cyd"] * BASE["rec_yd"]
            + d["ctd"] * BASE["rec_td"]) / 17.0

def rescore(preset, passtd=4.0):
    out = {}
    for pid, p in C.items():
        v = score(p, preset, passtd)
        if v is None:
            v = CUR.get(pid)
            if v != v or v is None:
                continue
            v = float(v)
        out[pid] = {"id": pid, "nm": p["nm"], "ps": p["ps"],
                    "tm": p["tm"], "ppg": round(v, 3),
                    "adp": ADP.get(pid),
                    "rk": RANK.get(pid)}
    return out

print("=== RE-SCORE SANITY ===")
fp = rescore("full_ppr")
print("  scored %d players under full PPR" % len(fp))
chk = [(v["nm"], v["ppg"], CUR.get(k))
       for k, v in fp.items()
       if v["nm"] in ("Josh Allen", "Puka Nacua",
                      "Brock Bowers", "Bijan Robinson")]
print("  %-20s %8s %8s" % ("player", "rescored", "board"))
for nm, a, b in chk:
    b = float(b) if b == b and b is not None else 0.0
    print("  %-20s %8.2f %8.2f  (%+.0f%%)"
          % (nm, a, b, 100.0 * (a / b - 1) if b else 0))
