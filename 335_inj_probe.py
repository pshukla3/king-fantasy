import json, ssl, certifi
import urllib.request as U

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}

print("=== ESPN league-wide injuries endpoint ===")
E = ("https://site.api.espn.com/apis/site/v2/"
     "sports/football/nfl/injuries")
try:
    r = U.Request(E, headers=H)
    d = json.loads(U.urlopen(r, timeout=25,
                             context=CTX).read())
    inj = d.get("injuries") or []
    print("teams: %d" % len(inj))
    tot = 0
    for t in inj:
        n = len(t.get("injuries") or [])
        tot += n
    print("total injury rows: %d" % tot)
    for t in inj[:2]:
        print("\nteam: %s" % t.get("displayName"))
        for i in (t.get("injuries") or [])[:3]:
            a = i.get("athlete") or {}
            de = i.get("details") or {}
            print("  %-22s %-12s %-10s ret=%s"
                  % (a.get("displayName"),
                     i.get("status"),
                     de.get("type"),
                     de.get("returnDate")))
            print("    keys: %s" % list(i.keys()))
            print("    dkeys: %s" % list(de.keys()))
except Exception as e:
    print("FAIL %s" % str(e)[:70])

print("\n=== nflverse injury history ===")
try:
    import nfl_data_py as nfl
    df = nfl.import_injuries([2023, 2024])
    print("rows %d  cols %d" % (len(df), len(df.columns)))
    print("columns: %s" % list(df.columns)[:18])
    c = ("report_primary_injury"
         if "report_primary_injury" in df.columns
         else df.columns[-1])
    print("\ntop injury types:")
    print(df[c].value_counts().head(14))
    if "report_status" in df.columns:
        print("\nstatuses:")
        print(df["report_status"].value_counts().head(6))
except ImportError:
    print("nfl_data_py NOT installed")
except Exception as e:
    print("FAIL %s" % str(e)[:70])
