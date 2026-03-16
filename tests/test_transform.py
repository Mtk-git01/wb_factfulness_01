import pandas as pd

from src.transform import prepare_country_year_u5mr


def test_prepare_country_year_u5mr_interpolates_missing_years():
    df = pd.DataFrame({
        "Country.Name": ["Japan", "Japan", "Japan"],
        "Country.ISO": ["JPN", "JPN", "JPN"],
        "Reference.Date": [2014.5, 2016.5, 2018.5],
        "Estimates": [40.0, 30.0, 20.0],
        "Standard.Error.of.Estimates": [4.0, 3.0, 2.0],
        "Inclusion": [1, 1, 1],
    })

    observed_df, interpolated_df = prepare_country_year_u5mr(df, "Japan")

    # Year Observed
    assert observed_df["Year"].tolist() == [2014, 2016, 2018]

    # 補間後は連続年
    assert interpolated_df["Year"].tolist() == [2014, 2015, 2016, 2017, 2018]

    # 2015 は 2014 と 2016 の中間
    val_2015 = interpolated_df.loc[interpolated_df["Year"] == 2015, "Estimates"].iloc[0]
    assert round(val_2015, 2) == 35.00

    # 補間フラグ
    flag_2015 = interpolated_df.loc[interpolated_df["Year"] == 2015, "is_interpolated"].iloc[0]
    assert bool(flag_2015) is True


def test_prepare_country_year_u5mr_accepts_iso_code():
    df = pd.DataFrame({
        "Country.Name": ["Japan"],
        "Country.ISO": ["JPN"],
        "Reference.Date": [2020.5],
        "Estimates": [10.0],
        "Inclusion": [1],
    })

    observed_df, interpolated_df = prepare_country_year_u5mr(df, "JPN")

    assert len(observed_df) == 1
    assert len(interpolated_df) == 1
    assert observed_df["Year"].iloc[0] == 2020