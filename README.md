# Bond Portfolio Dataset

This repository contains the current bond portfolio optimization and risk pipeline.

## What The Project Contains Right Now

The project currently has four main parts:

1. A synthetic bond universe in `data/` for optimizer and risk-engine testing.
2. A real bond universe in `real_data/` made from indexes and bond ETFs.
3. Covariance-construction experiments in `covariance_experiments/`.
4. A final optimizer-to-risk pipeline built around the synthetic bond universe.

## Main Scripts

- `mip_bond_optimizer.py`
  - Mixed-integer bond optimizer.
- `monte_carlo_engine.py`
  - Monte Carlo simulation and risk metric functions.
- `run_full_pipeline.py`
  - Runs the optimizer, evaluates covariance-based risk, runs Monte Carlo, and writes outputs.
- `run_covariance_experiments.py`
  - Benchmarks covariance matrix construction methods.

## Environment Setup

This repo now has a local virtual environment at `.venv/`.

Create it if needed:

```bash
python3 -m venv .venv
```

Install the pinned dependencies:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Run all project commands with the local interpreter:

```bash
.venv/bin/python ...
```

## How To Run The Optimizer

Run from the repo root:

```bash
.venv/bin/python mip_bond_optimizer.py
```

This loads:

- `data/synthetic_bond_universe.csv`
- `data/synthetic_covariance_matrix.csv`

It solves the predefined bond portfolio scenarios and prints scenario-level summary information.

## How To Run The Full Pipeline

Run from the repo root:

```bash
.venv/bin/python run_full_pipeline.py
```

This will:

1. Load the synthetic bond universe and covariance matrix.
2. Run all optimizer scenarios.
3. Save each optimal portfolio.
4. Run Monte Carlo simulation for each optimal portfolio.
5. Save simulated returns and Monte Carlo risk metrics.

## Notebook

- `notebooks/final_project_pipeline.ipynb`
  - Demonstrates the end-to-end workflow from loading data through Monte Carlo plots.

If you want to use the notebook with the repo-local environment, launch Jupyter from the virtual environment:

```bash
.venv/bin/python -m notebook
```

## Files Produced

The full pipeline writes files to `outputs/`:

- `outputs/portfolio_scenario_{id}.csv`
  - Optimized bond portfolio for a scenario.
- `outputs/mc_returns_scenario_{id}.csv`
  - Simulated portfolio returns from Monte Carlo.
- `outputs/mc_metrics_scenario_{id}.csv`
  - Monte Carlo summary risk metrics such as mean, standard deviation, VaR, and CVaR.
- `outputs/scenario_summary.csv`
  - Scenario-level summary table across all optimal scenarios.

## Brief Explanation Of Covariance Risk

The covariance matrix measures how bond returns move together. It is used to compute portfolio variance:

- `variance = w.T @ Sigma @ w`

where `w` is the portfolio weight vector and `Sigma` is the covariance matrix. Portfolio volatility is the square root of variance. This captures how individual bond risks combine at the portfolio level instead of treating each bond independently.

## Brief Explanation Of Monte Carlo Simulation

Monte Carlo simulation draws many possible return scenarios from a multivariate normal distribution using:

- expected asset returns
- portfolio weights
- the covariance matrix for the selected bonds

From those simulated portfolio returns, the pipeline computes:

- mean return
- standard deviation
- minimum and maximum simulated return
- VaR
- CVaR

This gives a distribution of possible outcomes instead of a single risk number.

## Folder Map

- `data/`
  - Synthetic bond universe, synthetic bond history, and synthetic covariance matrix.
- `real_data/`
  - Real bond indexes and ETFs with daily and monthly return outputs.
- `covariance_experiments/`
  - Covariance benchmark outputs and summary notes.
- `outputs/`
  - Final optimizer and Monte Carlo pipeline outputs.
- `Info_md's/`
  - Supporting markdown reference files for the project.
- `requirements.txt`
  - Pinned Python dependencies for the repo-local environment.
