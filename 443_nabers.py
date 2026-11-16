import json, re
import nflreadpy as nfl

def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()

WHO = ["Malik Nabers", "DJ Moore", "Jaxon Smith-Njigba",
       "Puka Nacua"]

B = json.load(open("site/_board.json"))
RS = json.load(open("site/_reasons.json"))
DC = json.load(open("site/_decomp.json"))
DR = {norm(r["n"]): r for r in json.load(open("site/_dr.json"))}
H = json.load(open("site/_hist.json"))

print("=== board rows ===")
for w in WHO:
    r = next((x for x in B["rows"]
              if norm(x["n"]) == norm(w)), None)
    if not r:
        print("  %s NOT ON BOARD" % w)
        continue
    print("  %-20s rk%-4s %s%-3s live %5.1f base %5.1f "
          "floor %4.1f ceil %5.1f adp %5.1f tier %s"
          % (r["n"][:20], r.get("rk"), r.get("pos"),
             r.get("posrk"), r.get("live"),
             r.get("base") or 0, r.get("floor") or 0,
             r.get("ceil") or 0, r.get("adp") or 0,
             r.get("tier")))
    print("       gm %s  games %s  inj %s  bye %s"
          % (r.get("gm"), r.get("games"), r.get("inj"),
             r.get("bye")))
    d = DR.get(norm(w))
    if d:
        print("       season proj: %s pts, %s tar, %s rec, "
              "%s yds, %s td"
              % (d.get("pts"), d.get("tar"), d.get("rec"),
                 d.get("cyd"), d.get("ctd")))
    rr = RS.get(norm(w))
    if rr:
        print("       reason: %s" % str(rr.get("line"))[:150])
    dd = DC.get(norm(w))
    if dd:
        print("       decomp: %s" % json.dumps(dd))
    hh = H.get(r.get("pid")) or []
    if hh:
        print("       last 8: %s"
              % ", ".join("%s%s:%.1f" % (x["t"], x["w"], x["p"])
                          for x in hh[-8:]))
    print()

print("=== what Next Gen Stats can give us ===")
for fn in ("load_nextgen_stats", "load_snap_counts",
           "load_ftn_charting", "load_pbp"):
    print("  %-22s %s" % (fn, hasattr(nfl, fn)))

try:
    n = nfl.load_nextgen_stats(seasons=[2025],
                               stat_type="receiving")
    n = n.to_pandas()
    print("\n  NGS receiving cols: %s" % list(n.columns))
    print("  rows: %d" % len(n))
except Exception as e:
    print("  NGS receiving failed: %s" % str(e)[:90])

try:
    s = nfl.load_snap_counts(seasons=[2025]).to_pandas()
    print("\n  snap cols: %s" % list(s.columns)[:18])
    print("  rows: %d" % len(s))
except Exception as e:
    print("  snaps failed: %s" % str(e)[:90])
