import os, ssl, certifi, io
import urllib.request as U
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
BASE = ("https://github.com/nflverse/nflverse-data/"
        "releases/download/injuries/injuries_%d.parquet")
os.makedirs("data_inj", exist_ok=True)

YRS = list(range(2016, 2026))
got = []
for y in YRS:
    p = "data_inj/inj_%d.parquet" % y
    if not os.path.exists(p):
        try:
            r = U.Request(BASE % y, headers=H)
            b = U.urlopen(r, timeout=60, context=CTX).read()
            open(p, "wb").write(b)
        except Exception as e:
            print("%d FAIL %s" % (y, str(e)[:44]))
            continue
    try:
        got.append(pd.read_parquet(p))
        print("%d ok %d rows" % (y, len(got[-1])))
    except Exception as e:
        print("%d READ FAIL %s" % (y, str(e)[:44]))

if not got:
    raise SystemExit("no injury data retrieved")

df = pd.concat(got, ignore_index=True)
print("\ntotal rows %d" % len(df))
print("columns: %s" % list(df.columns))
print("\nhead:")
print(df.head(3).to_string()[:900])

for c in ("report_status", "practice_status",
          "report_primary_injury"):
    if c in df.columns:
        print("\n%s:" % c)
        print(df[c].value_counts().head(10))
