# Covariance Matrix Experiments

These experiments benchmark covariance matrix construction on the real monthly bond return panel in `real_data/real_bond_monthly_returns.csv`.

## Methodology

- Base data: 28 real bond assets across 120 monthly observations from 2016-01 through 2025-12.
- Scaled universes: for N > 28, the script expands the observed real panel by cloning real asset return series with small noise and cross-asset mixing. This preserves the real-data backbone while making large-N timing experiments possible.
- Sample covariance: direct centered matrix multiplication.
- Factor covariance: four-factor model using monthly changes in 2Y Treasury, 10Y Treasury, 10Y-2Y slope, and BAA-AAA spread.
- Numeric precision: `float64` and `float32` are both benchmarked.

## Selected Results

- N=28: sample float64 0.0107 ms, factor float64 0.0776 ms, sample float32 matrix memory 0.0030 MB, factor-vs-sample relative error 0.6381
- N=56: sample float64 0.0147 ms, factor float64 0.0599 ms, sample float32 matrix memory 0.0120 MB, factor-vs-sample relative error 0.6604
- N=112: sample float64 0.0225 ms, factor float64 0.0674 ms, sample float32 matrix memory 0.0479 MB, factor-vs-sample relative error 0.6702
- N=224: sample float64 0.0585 ms, factor float64 0.0987 ms, sample float32 matrix memory 0.1914 MB, factor-vs-sample relative error 0.6709
- N=448: sample float64 0.2964 ms, factor float64 0.5314 ms, sample float32 matrix memory 0.7656 MB, factor-vs-sample relative error 0.6693
- N=896: sample float64 2.5667 ms, factor float64 3.3776 ms, sample float32 matrix memory 3.0625 MB, factor-vs-sample relative error 0.6734
- N=1792: sample float64 7.5463 ms, factor float64 5.7481 ms, sample float32 matrix memory 12.2500 MB, factor-vs-sample relative error 0.6730

## Output Files

- `covariance_experiments/covariance_benchmark_results.csv`
- `covariance_experiments/covariance_experiment_sizes.csv`

## Factor Columns

- `delta_treasury_2y`
- `delta_treasury_10y`
- `delta_treasury_slope_10y_2y`
- `delta_corp_baa_aaa_spread`
