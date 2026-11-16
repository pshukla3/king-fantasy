def season_split(df, test_season, season_col="season"):
    train = df[df[season_col] <= test_season - 2]
    val   = df[df[season_col] == test_season - 1]
    test  = df[df[season_col] == test_season]
    assert train[season_col].max() < val[season_col].min() < test[season_col].min()
    return train, val, test
