import pandas as pd
import requests
from io import BytesIO


def load_u5mr_data(url: str) -> pd.DataFrame:
    """
    URLからUN-IGME Excelを取得し、Total U5MRシートを読み込む。
    先頭2行は不要なので skiprows=2 で除外する。
    """
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    df = pd.read_excel(
        BytesIO(response.content),
        sheet_name="Total U5MR",
        skiprows=2
    )
    return df


def prepare_country_year_u5mr(df: pd.DataFrame, country_name_or_iso: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    指定国について、
    1) 観測値を1年1レコードに集約した observed_yearly
    2) 欠損年を線形補間した interpolated_yearly
    を返す。
    """
    required_cols = [
        "Country.Name",
        "Country.ISO",
        "Reference.Date",
        "Estimates",
        "Inclusion",
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")

    work = df.copy()

    # 対象国 + 採用観測のみ
    work = work[
        (work["Inclusion"] == 1)
        & (
            (work["Country.Name"] == country_name_or_iso)
            | (work["Country.ISO"] == country_name_or_iso)
        )
    ].copy()

    if work.empty:
        raise ValueError(f"No data found for: {country_name_or_iso}")

    # 数値変換
    work["Reference.Date"] = pd.to_numeric(work["Reference.Date"], errors="coerce")
    work["Estimates"] = pd.to_numeric(work["Estimates"], errors="coerce")

    if "Standard.Error.of.Estimates" in work.columns:
        work["Standard.Error.of.Estimates"] = pd.to_numeric(
            work["Standard.Error.of.Estimates"], errors="coerce"
        )

    work = work.dropna(subset=["Reference.Date", "Estimates"])

    # 年に変換
    work["Year"] = work["Reference.Date"].astype(float).astype(int)

    # 同一年に複数観測があれば平均
    agg_dict = {"Estimates": "mean"}
    if "Standard.Error.of.Estimates" in work.columns:
        agg_dict["Standard.Error.of.Estimates"] = "mean"

    observed_yearly = (
        work.groupby("Year", as_index=True)
        .agg(agg_dict)
        .sort_index()
    )

    if observed_yearly.empty:
        raise ValueError(f"No usable yearly data found for: {country_name_or_iso}")

    # 全年レンジを作って補間
    all_years = pd.Index(
        range(int(observed_yearly.index.min()), int(observed_yearly.index.max()) + 1),
        name="Year"
    )

    interpolated_yearly = observed_yearly.reindex(all_years)

    interpolated_yearly["Estimates"] = interpolated_yearly["Estimates"].interpolate(
        method="linear"
    )

    if "Standard.Error.of.Estimates" in interpolated_yearly.columns:
        interpolated_yearly["Standard.Error.of.Estimates"] = interpolated_yearly[
            "Standard.Error.of.Estimates"
        ].interpolate(method="linear")

    interpolated_yearly["is_interpolated"] = ~interpolated_yearly.index.isin(observed_yearly.index)

    return observed_yearly.reset_index(), interpolated_yearly.reset_index()