import ssl, certifi, os, glob
import urllib.request as U
import pandas as pd

CTX = ssl.create_default_context(cafile=certifi.where())
H = {"User-Agent": "curl/8.7.1"}
R = ("https://github.com/nflverse/nflverse-data/"
     "releases/download/")
T = "stats_player/stats_player_week_%d.parquet"
os.makedirs("data_usage", exist_ok=True)

def pull(url, path):
    if os.path.exists(path):
        return True
    try:
        b = U.urlopen(U.Request(url, headers=H),
                      timeout=90, context=CTX).read()
        open(path, "wb").write(b)
        return True
    except Exception as e:
        print("  FAIL %s" % str(e)[:40])
        return False

for y in range(2016, 2026):
    ok = pull(R + (T % y), "data_usage/wk_%d.parquet" % y)
    print("  wk %d %s" % (y, "ok" if ok else "-"))

pull(R + "snap_counts/snap_counts_2024.parquet",
     "data_usage/snaps_2024.parquet")

F = sorted(glob.glob("data_usage/wk_*.parquet"))
if F:
    D = pd.concat([pd.read_parquet(f) for f in F],
                  ignore_index=True)
    print("\nrows %d | seasons %s"
          % (len(D), sorted(D["season"].unique())))
    print("fantasy:", [c for c in D.columns
                       if "fantasy" in c.lower()])
    print("name:", [c for c in D.columns
                    if "name" in c.lower()][:4])
    D.to_parquet("weekly_all.parquet")
    print("wrote weekly_all.parquet")
