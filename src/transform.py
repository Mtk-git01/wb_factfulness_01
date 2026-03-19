from io import BytesIO
from typing import Optional, Tuple

import pandas as pd
import requests


def load_u5mr_data(url: str) -> pd.DataFrame:
    """
    UN-IGME Excel:Total U5MR sheet -> DataFrame
    """
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    df = pd.read_excel(
        BytesIO(response.content),
        sheet_name="Total U5MR",
        skiprows=2
    )

    required_cols = [
        "Country.Name",
        "Country.ISO",
        "Reference.Date",
        "Estimates",
        "Inclusion"
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    return df


def prepare_country_year_u5mr(df: pd.DataFrame, country_name_or_iso: str):
    df_filtered = df[
        (df["Inclusion"] == 1) &
        (
            (df["Country.Name"] == country_name_or_iso) |
            (df["Country.ISO"] == country_name_or_iso)
        )
    ].copy()

    if df_filtered.empty:
        return None, None

    # ---- to numeric ----
    df_filtered["Reference.Date"] = pd.to_numeric(
        df_filtered["Reference.Date"], errors="coerce"
    )
    df_filtered["Estimates"] = pd.to_numeric(
        df_filtered["Estimates"], errors="coerce"
    )

    if "Standard.Error.of.Estimates" in df_filtered.columns:
        df_filtered["Standard.Error.of.Estimates"] = pd.to_numeric(
            df_filtered["Standard.Error.of.Estimates"], errors="coerce"
        )
    else:
        df_filtered["Standard.Error.of.Estimates"] = pd.NA

    # Year
    df_filtered["Year"] = df_filtered["Reference.Date"].apply(
        lambda x: int(x) if pd.notnull(x) else pd.NA
    ).astype("Int64")

    # take mean 
    observed_df = (
        df_filtered
        .dropna(subset=["Year", "Estimates"])
        .groupby("Year", as_index=False)
        .agg({
            "Estimates": "mean",
            "Standard.Error.of.Estimates": "mean",
            "Country.Name": "first",
            "Country.ISO": "first",
        })
        .sort_values("Year")
        .reset_index(drop=True)
    )

    if observed_df.empty:
        return None, None

    min_year = int(observed_df["Year"].min())
    max_year = int(observed_df["Year"].max())

    all_years = pd.DataFrame({"Year": range(min_year, max_year + 1)})

    interpolated_df = (
        all_years
        .merge(
            observed_df[
                [
                    "Year",
                    "Estimates",
                    "Standard.Error.of.Estimates",
                    "Country.Name",
                    "Country.ISO",
                ]
            ],
            on="Year",
            how="left",
        )
        .sort_values("Year")
        .reset_index(drop=True)
    )

    # fill country iso
    interpolated_df["Country.Name"] = interpolated_df["Country.Name"].ffill().bfill()
    interpolated_df["Country.ISO"] = interpolated_df["Country.ISO"].ffill().bfill()

    # ---- interpolate into numeric ----
    interpolated_df["Estimates"] = pd.to_numeric(
        interpolated_df["Estimates"], errors="coerce"
    )
    interpolated_df["Standard.Error.of.Estimates"] = pd.to_numeric(
        interpolated_df["Standard.Error.of.Estimates"], errors="coerce"
    )

    # linear interpolate
    interpolated_df["Estimates"] = interpolated_df["Estimates"].interpolate(
        method="linear",
        limit_direction="both"
    )
    interpolated_df["Standard.Error.of.Estimates"] = interpolated_df[
        "Standard.Error.of.Estimates"
    ].interpolate(
        method="linear",
        limit_direction="both"
    )

    observed_years = set(observed_df["Year"].tolist())
    interpolated_df["is_interpolated"] = ~interpolated_df["Year"].isin(observed_years)

    return observed_df, interpolated_df