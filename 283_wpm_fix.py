import json
import math
import re

W = json.load(open("site/_wp.json"))
ING = W["mkt2"]
PRE = W["pregame"]
for k in ("feat", "mean", "scale", "coef", "intercept"):
    assert k in ING, "mkt2 missing %s" % k
n = len(ING["feat"])
assert len(ING["mean"]) == n and len(ING["scale"]) == n \
    and len(ING["coef"]) == n, "mkt2 array length mismatch"
assert isinstance(PRE.get("coef"), (int, float)), \
    "pregame coef should be scalar"
print("mkt2: %d features, intercept %+.4f"
      % (n, ING["intercept"]))
for f, c in sorted(zip(ING["feat"], ING["coef"]),
                   key=lambda x: -abs(x[1]))[:6]:
    print("    %-20s %+.4f" % (f, c))
print("pregame: intercept %+.4f, coef %+.4f (raw spread)"
      % (PRE["intercept"], PRE["coef"]))

def lg(z):
    return 1.0 / (1.0 + math.exp(-z))

def ft(sd, t, y, dn, ds, sp):
    t = max(1.0, t)
    return {"sd_t": sd / math.sqrt(t / 60.0 + 1),
            "expt": math.exp(-4.0 * t / 3600.0),
            "score_differential": sd, "t": t,
            "half": t if t <= 1800 else t - 1800,
            "down": dn, "ydstogo": ds,
            "yardline_100": y, "to_diff": 0,
            "is4": 1 if dn == 4 else 0,
            "spread_pos": sp, "sp_t": sp * (t / 3600.0)}

def ev(f):
    z = ING["intercept"]
    for i, k in enumerate(ING["feat"]):
        z += ING["coef"][i] * ((f.get(k, 0.0)
                                - ING["mean"][i])
                               / ING["scale"][i])
    return lg(z)

def evpre(sp):
    return lg(PRE["intercept"] + PRE["coef"] * sp)

print("\n=== SANITY (possessing/favored team) ===")
print("  %-34s %8s %9s" % ("state", "wp", "expect"))
print("  " + "-" * 55)
CK = [("pregame, favored by 7", evpre(7.0), "72-76%"),
      ("pregame, pick'em", evpre(0.0), "~49-51%"),
      ("pregame, dog by 7", evpre(-7.0), "24-28%"),
      ("tied, half, own 25, ball",
       ev(ft(0, 1800, 75, 1, 10, 0)), "50-56%"),
      ("up 7, 2:00, own 25, ball",
       ev(ft(7, 120, 75, 1, 10, 0)), "88-96%"),
      ("down 7, 2:00, own 25, ball",
       ev(ft(-7, 120, 75, 1, 10, 0)), "6-14%"),
      ("up 17, Q4 start, ball",
       ev(ft(17, 900, 75, 1, 10, 0)), "96-99%")]
bad = 0
for nm, v, exp in CK:
    lo, hi = [float(x.strip("%~ ")) / 100.0
              for x in exp.replace("~", "").split("-")]
    ok = (lo - 0.06) <= v <= (hi + 0.06)
    if not ok:
        bad += 1
    print("  %-34s %7.1f%% %9s %s"
          % (nm, 100 * v, exp, "" if ok else "<< OFF"))
if bad:
    print("\n%d checks off - NOT writing _game.js" % bad)
    raise SystemExit(1)
print("\nall checks pass - patching _game.js")

s = open("site/_game.js").read()
n0 = len(s)

MJ = json.dumps({"ing": {"feat": ING["feat"],
                         "mean": ING["mean"],
                         "scale": ING["scale"],
                         "coef": ING["coef"],
                         "i": ING["intercept"]},
                 "pre": {"i": PRE["intercept"],
                         "c": PRE["coef"]},
                 "ot": W.get("active", {}).get(
                     "ot_first_poss", 0.602)})
s2 = re.sub(r"^var M=\{.*?\};", "var M=" + MJ + ";",
            s, count=1, flags=re.M | re.S)
assert s2 != s, "could not replace M"
s = s2

NEWEV = ('function ev(m,f){if(!m||!m.feat)return 0.5;'
         'var z=m.i,i;for(i=0;i<m.feat.length;i++){'
         'z+=m.coef[i]*(((f[m.feat[i]]||0)-m.mean[i])'
         '/m.scale[i]);}return lg(z);}\n'
         'function evpre(sp){return lg(M.pre.i'
         '+M.pre.c*(sp||0));}')
s2 = re.sub(r"function ev\(m,f\)\{[\s\S]*?return lg\(z\);\}",
            NEWEV, s, count=1)
assert s2 != s, "could not replace ev()"
s = s2

a = "ev(M.pre,ft(0,3600,75,1,10,hAdv))"
assert a in s, "pregame call not found"
s = s.replace(a, "evpre(hAdv)", 1)

open("site/_game.js", "w").write(s)
print("_game.js %d -> %d bytes" % (n0, len(s)))
print("  standardization applied (mean/scale)")
print("  pregame now uses raw-spread scalar model")
