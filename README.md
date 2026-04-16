# Bond Portfolio Dataset

This folder contains the current working files for the bond portfolio optimization project.

## What The Project Contains Right Now

The project currently has three main parts:

1. A synthetic bond dataset for large-scale portfolio and risk experiments.
2. A real bond universe made of benchmark indexes and bond ETFs.
3. Covariance matrix experiments built on top of the real monthly return panel.

## Folder Map

### Top-level scripts

- `build_bond_dataset.py`
  - Builds the synthetic bond dataset in `data/`.
- `build_real_bond_dataset.py`
  - Builds the real bond dataset in `real_data/`.
- `run_covariance_experiments.py`
  - Runs the covariance construction benchmarks and writes outputs to `covariance_experiments/`.

### Synthetic dataset files

- `data/bond_factors_monthly.csv`
  - Monthly factor backbone used for the synthetic bond construction.
- `data/synthetic_bond_universe.csv`
  - Synthetic bond-level universe with bond type, rating, maturity, duration, liquidity, and related fields.
- `data/synthetic_bond_history.csv`
  - Monthly return history for the synthetic bonds.
- `data/synthetic_covariance_matrix.csv`
  - Covariance matrix built from the synthetic bond return history.
- `data/dataset_manifest.csv`
  - Row-count summary for the synthetic dataset outputs.

### Real dataset files

- `real_data/real_bond_asset_metadata.csv`
  - Asset list for the real bond universe.
- `real_data/real_bond_assets_daily.csv`
  - Daily asset levels for the real universe.
- `real_data/real_bond_daily_returns.csv`
  - Daily returns for the real universe.
- `real_data/real_bond_monthly_returns.csv`
  - Main monthly return panel for the real universe.
- `real_data/real_bond_factors_monthly.csv`
  - Monthly macro and bond factor series used with the real dataset.
- `real_data/real_bond_daily_covariance_matrix.csv`
  - Daily covariance matrix for the real universe.
- `real_data/real_bond_monthly_covariance_matrix.csv`
  - Monthly covariance matrix for the real universe.
- `real_data/real_dataset_manifest.csv`
  - Row-count summary for the real dataset outputs.

### Covariance experiment files

- `covariance_experiments/covariance_benchmark_results.csv`
  - Benchmark results for covariance matrix construction.
- `covariance_experiments/covariance_experiment_sizes.csv`
  - The asset sizes used in the covariance scaling tests.
- `covariance_experiments/covariance_experiment_summary.md`
  - Short written summary of the covariance experiment setup and results.

### Documentation files

- `REAL_DATASET.md`
  - Notes on how the real dataset is constructed.
- `REAL_BOND_UNIVERSE.md`
  - List of the indexes and ETFs used in the real bond universe.
- `COVARIANCE_EXPERIMENTS.md`
  - Notes on how to run the covariance experiments.
- `SOURCES.md`
  - Source notes for the datasets reviewed and used.

## Most Important Files

If you are working with the real-data version of the project, the main files are:

- `real_data/real_bond_asset_metadata.csv`
- `real_data/real_bond_monthly_returns.csv`
- `real_data/real_bond_factors_monthly.csv`
- `covariance_experiments/covariance_benchmark_results.csv`
- `REAL_BOND_UNIVERSE.md`

If you are working with the synthetic-data version of the project, the main files are:

- `data/synthetic_bond_universe.csv`
- `data/synthetic_bond_history.csv`
- `data/synthetic_covariance_matrix.csv`

## Rebuild Commands

Run these from the project folder if you need to regenerate outputs:

```bash
python3 /Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/build_bond_dataset.py
python3 /Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/build_real_bond_dataset.py
python3 /Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/run_covariance_experiments.py
```
