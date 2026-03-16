# wb_factfulness_01

A small reproducible development-data project using the UN-IGME observational database on under-five mortality.

## Project purpose
This project demonstrates a simple country-year data pipeline for public development indicators.

## What it does
- Reads the `Total U5MR` sheet from the UN-IGME Excel source
- Removes the first two non-data rows
- Filters to included observations only
- Aggregates irregular observations into one country-year record
- Applies linear interpolation to create a continuous annual trend
- Flags interpolated values separately from observed values
- Produces CSV outputs and a trend chart

## Important note
This project uses the UN-IGME observational database, not the official UN-IGME modelled estimates.

`Standard.Error.of.Estimates` in the source file refers to the sampling standard error of the underlying empirical observation, not the uncertainty of the final UN-IGME modelled estimate.

## Repository structure
```text
wb_factfulness_01/
├── README.md
├── requirements.txt
├── src/
│   ├── main.py
│   └── transform.py
├── tests/
│   └── test_transform.py
└── .github/
    └── workflows/
        └── ci.yml