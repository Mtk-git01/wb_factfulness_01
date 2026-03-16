from pathlib import Path

import matplotlib.pyplot as plt

from transform import load_u5mr_data, prepare_country_year_u5mr


U5MR_URL = "https://childmortality.org/wp-content/uploads/2024/03/UNIGME-2024-Total-U5MR-IMR-and-NMR-database.xlsx"
TARGET_COUNTRY = "Kenya"


def main() -> None:
    df = load_u5mr_data(U5MR_URL)
    observed_df, interpolated_df = prepare_country_year_u5mr(df, TARGET_COUNTRY)

    print("=== Interpolated yearly data ===")
    print(interpolated_df.tail(10))
    print("\n=== Observed yearly average data ===")
    print(observed_df.tail(10))

    # Output
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    # CSV
    observed_df.to_csv(output_dir / f"observed_u5mr_{TARGET_COUNTRY}.csv", index=False)
    interpolated_df.to_csv(output_dir / f"interpolated_u5mr_{TARGET_COUNTRY}.csv", index=False)

    # plt
    plt.figure(figsize=(12, 7))

    plt.plot(
        interpolated_df["Year"],
        interpolated_df["Estimates"],
        linestyle="-",
        label="Interpolated yearly U5MR"
    )

    plt.scatter(
        observed_df["Year"],
        observed_df["Estimates"],
        s=50,
        label="Observed yearly average"
    )

    if "Standard.Error.of.Estimates" in interpolated_df.columns:
        se = interpolated_df["Standard.Error.of.Estimates"]
        lower_bound = interpolated_df["Estimates"] - 1.96 * se
        upper_bound = interpolated_df["Estimates"] + 1.96 * se

        plt.fill_between(
            interpolated_df["Year"],
            lower_bound,
            upper_bound,
            alpha=0.2,
            label="95% Confidence Interval"
        )

    plt.title(f"Under-five Mortality Rate (U5MR): {TARGET_COUNTRY}")
    plt.xlabel("Year")
    plt.ylabel("Deaths per 1,000 live births")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"mortality_trend_interpolated_{TARGET_COUNTRY}.png", dpi=300)
    plt.close()


if __name__ == "__main__":
    main()