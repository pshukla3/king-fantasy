import nflreadpy as nfl
import pandas as pd

ids_polars = nfl.load_ff_playerids()
ids = ids_polars.to_pandas()

print("Shape:", ids.shape)
print("Columns:", list(ids.columns))
print(ids.head())

ids.to_csv("player_id_crosswalk.csv", index=False)
print("\nSaved to player_id_crosswalk.csv")
