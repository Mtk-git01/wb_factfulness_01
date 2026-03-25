# Factfulness-inspired Development Data Dashboard  
## Bridging public perception and observed development outcomes

A portfolio project that combines **public-sector data engineering**, **development indicator processing**, and **interactive communication** through an R Shiny dashboard.

This project is inspired by the central idea of *Factfulness*: public perceptions about the world often diverge from measured long-run development outcomes. To make that contrast more concrete, I built a small but reproducible workflow that links a perception-based “Negativity Instinct” measure with official development indicators, then presents the results in an interactive country-level dashboard.

The project is designed to demonstrate skills directly relevant to development statistics work:

- transforming raw public indicator data into usable country-year analytical datasets
- documenting assumptions and limitations transparently
- handling missingness in a reproducible way
- combining statistical interpretation with policy-facing visualization
- communicating indicator caveats clearly rather than hiding them

## Live dashboard
- **R Shiny app**: https://mtk01.shinyapps.io/wb_factfulness/

---

## Why this project
A common challenge in development analytics is that public narratives are often shaped by perception, while policy decisions require interpretable evidence from structured datasets. This project addresses that gap by comparing:

- a **perception-oriented measure** derived from a Factfulness-related chart
- **Under-five mortality rate (U5MR)** as a child survival outcome
- **Girls’ primary completion rate** as a basic education outcome

The result is a small interactive dashboard that helps users move from broad perception to measurable country-level evidence.

---

## What this repository demonstrates

This repository shows how I approach development-data work end to end:

### 1. Data preparation
I convert raw public-source files into clean country-year datasets suitable for analysis and visualization.

### 2. Reproducibility
I separate extraction, transformation, interpolation, and dashboard presentation so each step can be reviewed and improved independently.

### 3. Transparency
I explicitly describe data limitations, interpolation logic, and metadata caveats, especially where source definitions are easy to misinterpret.

### 4. Communication
I translate technical datasets into an interactive dashboard that is readable to non-technical stakeholders while preserving methodological clarity.

---

## Indicators included

### 1. Negativity Instinct ratio
A perception-oriented metric reconstructed from a published chart image associated with the Factfulness narrative. This is used as a demonstration of chart-to-data extraction when a machine-readable source is not directly available.

### 2. Under-five mortality rate (U5MR)
A child survival indicator built from the UN-IGME observational database and transformed into a country-year annual series.

### 3. Girls’ primary completion rate
A country-year education indicator based on **Primary completion rate, female (% of relevant age group)** with indicator code:

`SE.PRM.CMPT.FE.ZS`

In the dashboard, users can switch between **U5MR** and **Girls’ primary completion** for the selected country.

---

## Data architecture and upstream pipeline

This repository is intentionally positioned as the **dashboard and analytical interpretation layer** of a broader development-statistics workflow.

The broader analytical data foundation behind this project — including **Azerbaijan CPF-style macro-financial analysis, banking operations and financial access monitoring, trade and payments data, and cross-country development indicators** — is maintained in the companion repository:

- **Upstream pipeline and analytical data foundation**:    
  [wb_dev_data_pipeline (Azerbaijan CPF - The Elusive Quest for Growth)](https://github.com/Mtk-git01/wb_dev_data_pipeline)

That companion repository serves as the upstream backbone for:

- Azerbaijan-focused CPF and macro-financial analysis
- banking operations and financial-access monitoring with Central Bank based dashboard
- trade, payments, and external-sector indicator processing
- public development indicator transformation and validation
- BigQuery-ready analytical table creation for downstream dashboards and interpretation

In practical terms:

- **`wb_dev_data_pipeline`** = upstream analytical foundation, data engineering, and curation layer with dashboard
- **this repository** = downstream dashboard, interpretation, and statistical communication layer

This separation is deliberate. It reflects how production-oriented statistical work is often structured: source ingestion and transformation are handled upstream, while analysis, interpretation, and dissemination sit downstream.

---

## Data sources

### Perception data
- Factfulness / Gapminder-style visualization based on survey results from **YouGov** and **Ipsos MORI**
- Reconstructed here from a chart image for portfolio purposes, to demonstrate image-based extraction where direct tabular access is not available

### Child mortality data
- **UN Inter-agency Group for Child Mortality Estimation (UN IGME)** observational database
- Source URL: https://childmortality.org/

### Girls’ primary completion data
- Country-year education indicator for **Primary completion rate, female (% of relevant age group)**
- Indicator code: `SE.PRM.CMPT.FE.ZS`

---

## Methodology

## 1. Source data preparation

### U5MR
The U5MR workflow reads the observational database and:

- removes non-data header rows
- keeps included observations
- converts irregular reference dates into annual time points
- aggregates multiple observations within the same year into a single annual country-year record

This produces an analysis-ready annual panel while preserving a clear link to the original observational source.

### Girls’ primary completion
The girls’ education workflow:

- standardizes country names and ISO3 codes
- converts year and value fields into numeric analytical types
- filters the dataset to the relevant female primary completion indicator
- prepares a country-year series for dashboard use

---

## 2. Treatment of missing data

Development indicators often contain gaps, irregular observation timing, and cross-country comparability issues. Instead of obscuring this, I make the treatment explicit.

### U5MR
The annual U5MR series includes interpolation flags where values are carried into a continuous annual sequence for visualization and comparison.

### Girls’ primary completion
For girls’ primary completion, I apply **linear interpolation only to internal missing years within a country series**.

This means:

- missing values between two observed years may be interpolated
- leading missing values are not extrapolated
- trailing missing values are not extrapolated
- interpolated observations are explicitly marked in the dashboard

This approach is intentionally conservative: it supports continuity for visual interpretation without pretending to recover information beyond the observed range.

### Linear interpolation formula
If a value is observed at year `x0` and another value is observed at year `x1`, then the interpolated value at year `x` is:

`y(x) = y0 + ((x - x0) / (x1 - x0)) * (y1 - y0)`

where:

- `x0` = earlier observed year
- `x1` = later observed year
- `y0` = observed value at `x0`
- `y1` = observed value at `x1`

---

## 3. Image-based extraction of perception data

A machine-readable perception dataset was not directly available for the chart used in this project, so I implemented an image-based extraction workflow.

The process:

- loads the chart image
- converts it to grayscale
- applies thresholding to isolate bar structures
- uses morphological operations to connect fragmented regions
- detects horizontal bar contours
- converts bar length into approximate percentages using manually specified anchor points

This is included as a practical example of extracting structured evidence from a visual source when published material is not distributed in tabular form.

### Debug excerpt
A reduced debug excerpt is included to illustrate the extraction logic used in this repository.

> Note: The original chart image is not redistributed in full here for copyright reasons. The repository includes the extraction code, a debug excerpt, and the derived dataset used in the dashboard.

<p align="center">
  <img src="images/chart_extraction_debug_excerpt.png" alt="Partial chart extraction debug view" width="700">
</p>

---

## Dashboard features

The R Shiny dashboard includes:

- an interactive world map colored by Negativity Instinct ratio
- click-based country selection
- a country summary panel
- a toggle between:
  - **U5MR**
  - **Girls’ primary completion**
- a U5MR time-series view with confidence interval band where available
- a girls’ primary completion time-series view
- interpolation markers for completion-rate estimates
- a 100% reference line for the completion-rate series
- a metadata panel describing data source and interpolation share

For interpretability, the Girls’ primary completion plot begins at **1995**, which improves readability for recent decades and reduces unnecessary empty historical space.

---

## Important interpretation notes

### 1. U5MR source interpretation
This project uses the **UN-IGME observational database**, not the final UN-IGME modelled estimate series.

Also, `Standard.Error.of.Estimates` refers to the sampling error of the underlying empirical observation, not the uncertainty interval of the final published modelled estimate.

### 2. Completion rates can exceed 100
The girls’ primary completion rate may exceed **100%**. This can happen because the numerator may include over-age and under-age entrants to the final primary grade, while the denominator is the population of official graduation age.

This is an important statistical caveat, and I preserve it explicitly in both the code and the dashboard notes.

### 3. Interpolation is a visualization aid
Interpolation is used here to create smoother analytical series and make gaps more interpretable. It is not presented as a substitute for official source methodology.

### 4. Perception extraction is approximate
The chart-based perception dataset is an approximate reconstruction and is included for methodological demonstration rather than as an official survey microdata product.

---

## Repository structure

```text
wb_factfulness_01/
├── README.md
├── requirements.txt
├── src/
│   ├── main.py
│   └── transform.py
├── scripts/
│   └── extract_perception_from_chart.py
├── tests/
│   └── test_transform.py
├── images/
│   └── chart_extraction_debug_excerpt.png
├── R_shiny_app/
│   ├── app.R
│   ├── world_getting_worse_extracted.csv
│   ├── u5mr_country_year_all_countries.csv
│   └── girls_primary_completion_country_year.csv
└── .github/
    └── workflows/
        └── ci.yml
```

## Why this matters for development statistics

This project is meant to be small enough to review quickly, but rich enough to demonstrate core competencies relevant to development-statistics work:

- working with imperfect public datasets
- transforming irregular source structures into analytical panels
- documenting assumptions clearly
- balancing statistical caution with practical usability
- presenting results in a form that supports communication, not just computation

In that sense, the project is less about building a flashy dashboard and more about showing a disciplined workflow from source data to interpretable evidence.

--- 
### Portfolio positioning

Together, this repository and the upstream wb_dev_data_pipeline repository show two complementary capabilities:

### Upstream
- ingestion
- cleaning
- validation
- structured storage
reproducible transformation
### Downstream
- indicator interpretation
- missing-data handling
- methodological transparency
- interactive dissemination

That combination reflects the type of work often required in statistical and development-data roles: not only producing datasets, but ensuring that they can be understood, scrutinized, and used.

--- 
## Possible next extensions

Potential future enhancements include:

- adding more education, health, and inclusion indicators
- expanding metadata panels with source notes and definitional caveats
- connecting directly to curated BigQuery outputs from the upstream pipeline
- adding downloadable country profiles for policy-style dissemination