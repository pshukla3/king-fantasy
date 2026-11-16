import os, ssl, certifi
import urllib.request as U
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
R = "https://github.com/nflverse/nflverse-data/releases/download/"
os.makedirs("data_usage", exist_ok=True)

SRC = [
 ("snaps", R + "snap_counts/snap_counts_%d.parquet"),
 ("ngs_rec", R + "nextgen_stats/ngs_%d_receiving.parquet"),
 ("ngs_pass", R + "nextgen_stats/ngs_%d_passing.parquet"),
 ("ngs_rush", R + "nextgen_stats/ngs_%d_rushing.parquet"),
 ("pfr_rec", R + "pfr_advstats/advstats_season_rec.parquet"),
 ("pfr_pass", R + "pfr_advstats/advstats_season_pass.parquet"),
]

def get(url, path):
    if os.path.exists(path):
        return True
    try:
        b = U.urlopen(U.Request(url, headers=H),
                      timeout=90, context=CTX).read()
        open(path, "wb").write(b)
        return True
    except Exception as e:
        print("   FAIL %s" % str(e)[:60])
        return False

for name, tpl in SRC:
    print("\n=== %s ===" % name)
    if "%d" in tpl:
        ok = get(tpl % 2024, "data_usage/%s_2024.parquet"
                 % name)
        p = "data_usage/%s_2024.parquet" % name
    else:
        ok = get(tpl, "data_usage/%s.parquet" % name)
        p = "data_usage/%s.parquet" % name
    if not ok:
        continue
    try:
        d = pd.read_parquet(p)
    except Exception as e:
        print("   READ FAIL %s" % str(e)[:50])
        continue
    print("   rows %d" % len(d))
    cols = list(d.columns)
    print("   cols: %s" % cols[:26])
    for want in ("separation", "cushion", "routes",
                 "snap", "time_to_throw", "cpoe",
                 "expected", "air_yards", "pct"):
        hit = [c for c in cols if want in c.lower()]
        if hit:
            print("   *%-12s %s" % (want, hit[:6]))
