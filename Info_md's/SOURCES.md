# Sources Reviewed

## Directly used in the built dataset

1. FRED: Moody's Seasoned Aaa Corporate Bond Yield (`AAA`)
   - URL: https://fred.stlouisfed.org/series/AAA
   - Used for: investment-grade corporate yield level and spread construction.

2. FRED: Moody's Seasoned Baa Corporate Bond Yield (`BAA`)
   - URL: https://fred.stlouisfed.org/series/BAA
   - Used for: lower-investment-grade corporate yield level and spread construction.

3. FRED Treasury constant maturity series
   - Example URL: https://fred.stlouisfed.org/series/GS10
   - Used series: `GS1`, `GS2`, `GS5`, `GS10`, `GS20`, `GS30`
   - Used for: Treasury curve level, slope, and duration-sensitive factor moves.

## Reviewed as part of the proposal source list

4. U.S. Treasury daily yield curve page
   - URL: https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve
   - Role: confirms the official Treasury source family for daily government yield data.

5. Jordà-Schularick-Taylor Macrohistory Database
   - URL: https://www.macrohistory.net/database/
   - Role: long-run historical reference reviewed from the proposal's NBER-style macrohistory source family.
   - Not merged into the main dataset because the proposal's build target was a unified recent-period panel, while this database is oriented toward long-run historical coverage and different frequencies.

6. EMMA / MSRB municipal market data
   - URL: https://emma.msrb.org/
   - Role: reviewed as the municipal bond source named in the proposal.
   - Not directly merged because the public site is workflow-oriented rather than a simple stable bulk CSV endpoint for this build.

7. Kaggle corporate bond index datasets
   - Example search landing page: https://www.kaggle.com/
   - Role: reviewed as the proposal's index source family.
   - Not used in the automated build because Kaggle datasets generally require account-authenticated access and would make the pipeline non-reproducible on a clean machine.

## Why the final dataset is partly synthetic

The time-series factors are real public market data. The bond-level universe is synthetic so the dataset can support:

- large covariance matrices,
- minimum-increment constraints,
- bond-type allocation constraints,
- liquidity bands,
- Monte Carlo and stress-testing experiments,
- scalability tests as portfolio size increases.

That matches the proposal's stated plan to increase portfolio size by expanding the bond universe and generating larger simulated portfolios.
