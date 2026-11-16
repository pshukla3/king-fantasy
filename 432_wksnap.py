import json, os, re

OUT = "site/_wkproj.json"
SNAP = json.load(open(OUT)) if os.path.exists(OUT) else {}


def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def nflweek():
    import datetime
    A = datetime.datetime(2026, 9, 8,
                          tzinfo=datetime.timezone.utc)
    d = (datetime.datetime.now(datetime.timezone.utc) - A)
    return max(1, min(18, d.days // 7 + 1))


CUR = nflweek()
print("current week: %d" % CUR)

# --- seed week 1 from the accuracy file ---------------
if "1" not in SNAP and os.path.exists("site/_wk1.json"):
    W = json.load(open("site/_wk1.json"))
    rows = W.get("rows", [])
    if rows:
        ks = list(rows[0].keys())
        print("_wk1 row keys: %s" % ks)
        pf = None
        for c in ("proj", "projected", "pred", "p",
                  "exp", "base"):
            if c in rows[0]:
                pf = c
                break
        nf = None
        for c in ("n", "name", "player"):
            if c in rows[0]:
                nf = c
                break
        if pf and nf:
            SNAP["1"] = {norm(r[nf]): round(float(r[pf]), 2)
                         for r in rows
                         if r.get(pf) is not None}
            print("seeded week 1 from _wk1.json: "
                  "%d players (field %r)"
                  % (len(SNAP["1"]), pf))
        else:
            print("could NOT find projection/name fields "
                  "in _wk1.json -- keys were %s" % ks)

# --- snapshot the current week, never overwrite -------
k = str(CUR)
if k in SNAP:
    print("week %d already snapshotted (%d players) "
          "- leaving it alone" % (CUR, len(SNAP[k])))
else:
    B = json.load(open("site/_board.json"))
    cur = {}
    for r in B.get("rows", []):
        v = r.get("live")
        if v is None:
            continue
        key = (str(r.get("tm")) if str(r.get("pos")) in
               ("DEF", "DST") else norm(r.get("n")))
        cur[key] = round(float(v), 2)
    SNAP[k] = cur
    print("snapshotted week %d: %d projections"
          % (CUR, len(cur)))

json.dump(SNAP, open(OUT, "w"), separators=(",", ":"))
print("wrote %s (weeks: %s, %d KB)"
      % (OUT, ", ".join(sorted(SNAP, key=int)),
         os.path.getsize(OUT) // 1024))
