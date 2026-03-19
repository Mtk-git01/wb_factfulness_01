from pathlib import Path
import pandas as pd

from transform import load_u5mr_data, prepare_country_year_u5mr

U5MR_URL = "https://childmortality.org/wp-content/uploads/2024/03/UNIGME-2024-Total-U5MR-IMR-and-NMR-database.xlsx"


def get_all_countries(df: pd.DataFrame) -> list[str]:
    return (
        df.loc[df["Inclusion"] == 1, "Country.Name"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )


def main() -> None:
    df = load_u5mr_data(U5MR_URL)
    countries = get_all_countries(df)

    all_rows = []

    for country in countries:
        observed_df, interpolated_df = prepare_country_year_u5mr(df, country)

        if observed_df is None or interpolated_df is None:
            print(f"Skipping {country}: no usable data")
            continue

        # Streamlit用に列名を整理
        out = interpolated_df.copy()
        out["country_name"] = country

        # ISOコードも付けたい場合
        country_iso = (
            df.loc[df["Country.Name"] == country, "Country.ISO"]
            .dropna()
            .astype(str)
        )
        out["country_iso"] = country_iso.iloc[0] if len(country_iso) > 0 else None

        # 列名をStreamlit側に合わせる
        rename_map = {
            "Year": "year",
            "Estimates": "u5mr_estimate",
            "Standard.Error.of.Estimates": "standard_error_of_estimates",
        }
        out = out.rename(columns=rename_map)

        # is_interpolated を付与
        if "is_interpolated" not in out.columns:
            observed_years = set(observed_df["Year"].tolist())
            out["is_interpolated"] = ~out["year"].isin(observed_years)

        all_rows.append(
            out[
                [
                    "country_name",
                    "country_iso",
                    "year",
                    "u5mr_estimate",
                    "standard_error_of_estimates",
                    "is_interpolated",
                ]
            ]
        )

    final_df = pd.concat(all_rows, ignore_index=True).sort_values(
        ["country_name", "year"]
    )

    output_path = Path("streamlit_app/u5mr_country_year_all_countries.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"Saved: {output_path}")
    print(final_df.head())
    print(final_df.shape)


if __name__ == "__main__":
    main()