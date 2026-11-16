import nflreadpy as nfl
from pathlib import Path

SEASONS = list(range(2016, 2026))
OUT = Path("data"); OUT.mkdir(exist_ok=True)

pbp = nfl.load_pbp(seasons=SEASONS)
pbp.write_parquet(OUT / "pbp.parquet")
print(pbp.shape)
print(pbp.select(["season", "week", "posteam", "play_type", "down", "ydstogo",
                  "yardline_100", "ep", "epa", "wp", "cp", "xpass"]).head())
print("max season:", pbp["season"].max())
