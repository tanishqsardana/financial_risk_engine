# Bond Portfolio Dataset

This repository contains the current bond portfolio optimization and risk pipeline.

## Project Contents 

The project has five main parts:

1. A synthetic bond universe in `data/` for optimizer and risk-engine testing.
2. A real bond universe in `real_data/` made from indexes and bond ETFs.
3. Covariance-construction experiments in `covariance_experiments/`.
4. A final optimizer-to-risk pipeline built around the synthetic bond universe.
5. A high-performance optimized pipeline (`*_optimized.py`) with individualized technique timing in comparison to the baseline counterpart.

## Main Scripts

### Baseline Pipeline

- `mip_bond_optimizer.py`
  - Mixed-integer bond optimizer.
- `monte_carlo_engine.py`
  - Monte Carlo simulation and risk metric functions.
- `stress_testing_engine.py`
  - Stress testing utilities for covariance and return shocks.
- `solver_comparison.py`
  - Continuous mean-variance solver comparison for OSQP and SLSQP.
- `factor_covariance_benchmark.py`
  - Factor covariance construction and covariance benchmarking utilities.
- `run_full_pipeline.py`
  - Runs the optimizer, evaluates covariance-based risk, runs Monte Carlo, stress tests, solver comparison, and factor covariance benchmarks.
- `run_covariance_experiments.py`
  - Benchmarks covariance matrix construction methods.

### Optimized Pipeline

Each baseline script has an `_optimized.py` counterpart with one or more performance techniques applied. `run_full_pipeline_optimized.py` times every technique (labeled T*) individually against the baseline and prints a single summary DataFrame.

- `mip_bond_optimizer_optimized.py`
  - T1: vectorized covariance slicing via numpy integer-index map instead of pandas `.loc`.
  - T2: parallel MIP scenario solving — `multiprocessing.Pool` dispatches all 7 scenarios concurrently, with one worker dispatched per scenario.
- `monte_carlo_engine_optimized.py`
  - T3: Cython inner loop via `mc_core.pyx` — numpy generates standard normals, Cython typed memoryview loop applies the Cholesky transform and portfolio dot product.
  - T4: multiprocessing chunk split — `Pool` divides `n_simulations` across CPU cores.
- `stress_testing_engine_optimized.py`
  - T5: parallel stress scenarios — `Pool` runs all 4 stress scenarios concurrently.
- `solver_comparison_optimized.py`
  - T6: parallel solver calls — `ThreadPoolExecutor` runs CVXPY/OSQP and SciPy/SLSQP simultaneously.
- `factor_covariance_benchmark_optimized.py`
  - T7: parallel benchmark sizes — `ProcessPoolExecutor` benchmarks all asset-count sizes concurrently.
- `mc_core.pyx`
  - Cython extension source for the Monte Carlo inner loop. Must be compiled before running the optimized pipeline (see below).
- `setup_mc_cython.py`
  - Build script for `mc_core.pyx`, to be able to run Cython inner loop. of monte carlo engine 

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

The optimized pipeline requires two additional packages not in `requirements.txt`:

```bash
pip install cython numpy
```

Activate the environment:

```bash
source .venv/bin/activate
```

After activation, run project commands with `python` from the repo root.

## How To Run The Optimizer

Run from the repo root:

```bash
python mip_bond_optimizer.py
```

This loads:

- `data/synthetic_bond_universe.csv`
- `data/synthetic_covariance_matrix.csv`

It solves the predefined bond portfolio scenarios and prints scenario-level summary information.

## How To Run The Full Pipeline

Run from the repo root:

```bash
python run_full_pipeline.py
```

This will:

1. Load the synthetic bond universe and covariance matrix.
2. Run all optimizer scenarios.
3. Save each optimal portfolio.
4. Run Monte Carlo simulation for each optimal portfolio.
5. Run stress tests for each optimal scenario.
6. Run a continuous solver comparison.
7. Run a factor covariance benchmark.
8. Save all generated outputs.

## How To Run The Optimized Pipeline

Build the Cython extension once before first use:

```bash
python setup_mc_cython.py build_ext --inplace
```

Then run the optimized pipeline:

```bash
python run_full_pipeline_optimized.py
```

This runs the same end-to-end pipeline using all seven optimization techniques, times each one individually against the baseline, and prints a single summary DataFrame.

## Notebook

- `notebooks/final_project_pipeline.ipynb`
  - Demonstrates the end-to-end workflow from loading data through Monte Carlo plots.

If you want to use the notebook with the repo-local environment, launch Jupyter from the virtual environment:

```bash
python -m notebook
```

## Standalone Factor Benchmark

Run the factor covariance benchmark directly from the repo root:

```bash
python factor_covariance_benchmark.py
```

## Files Produced

Both pipelines write files to `outputs/`. The optimized pipeline writes the same files with an `_optimized` suffix where applicable.

**Baseline (`run_full_pipeline.py`)**

- `outputs/portfolio_scenario_{id}.csv`
  - Optimized bond portfolio for a scenario.
- `outputs/mc_returns_scenario_{id}.csv`
  - Simulated portfolio returns from Monte Carlo.
- `outputs/mc_metrics_scenario_{id}.csv`
  - Monte Carlo summary risk metrics such as mean, standard deviation, VaR, and CVaR.
- `outputs/stress_metrics_scenario_{id}.csv`
  - Stress-test Monte Carlo metrics for baseline, covariance stress, return shock, and combined stress.
- `outputs/scenario_summary.csv`
  - Scenario-level summary table across all optimal scenarios.
- `outputs/solver_comparison.csv`
  - Continuous mean-variance solver comparison results.
- `outputs/factor_covariance_benchmark.csv`
  - Runtime and memory benchmark for factor covariance and sample covariance methods.

**Optimized (`run_full_pipeline_optimized.py`)**

- `outputs/portfolio_scenario_{id}.csv` — same format, written by optimized solve.
- `outputs/mc_returns_scenario_{id}.csv` — produced via Cython/parallel Monte Carlo.
- `outputs/mc_metrics_scenario_{id}.csv` — risk metrics from optimized MC.
- `outputs/stress_metrics_scenario_{id}.csv` — produced via parallel stress engine.
- `outputs/scenario_summary_optimized.csv` — scenario summary from parallel solve.
- `outputs/solver_comparison_optimized.csv` — solver comparison from parallel run.
- `outputs/factor_covariance_benchmark_optimized.csv` — benchmark from parallel run.

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

## Stress Testing

Stress testing extends the Monte Carlo engine with simplified adverse scenarios:

- covariance stress
  - scales the covariance matrix upward
- return shock
  - reduces expected annual returns
- combined stress
  - applies both shocks together

This helps compare how the same portfolio behaves under normal assumptions versus a deliberately harsher setup.

## Solver Comparison

The solver comparison module does not rerun the integer MIP directly with multiple solvers. Instead, it uses a relaxed continuous mean-variance optimization problem so that:

- CVXPY with OSQP can be tested
- SciPy with SLSQP can be tested

This keeps the comparison lightweight and robust, but it is not an apples-to-apples replacement for the integer portfolio construction model.

## Factor Covariance Benchmark

The factor covariance benchmark uses the synthetic bond universe factor betas:

- `level_beta`
- `slope_beta`
- `spread_ig_beta`
- `spread_hy_beta`
- `muni_beta`
- `fx_beta`

It builds an approximate covariance matrix from those betas and compares that construction path against sample covariance when matching return history is available.

## Limitations

- The MIP optimizer and the continuous solver comparison are not the same formulation.
- The stress tests are simplified shocks, not a full macro scenario framework.
- The factor covariance matrix is approximate and partly synthetic, intended for benchmarking and scaling demonstration rather than market-calibrated production risk modeling.

## Folder Map

- `data/`
  - Synthetic bond universe, synthetic bond history, and synthetic covariance matrix.
- `real_data/`
  - Real bond indexes and ETFs with daily and monthly return outputs.
- `covariance_experiments/`
  - Covariance benchmark outputs and summary notes.
- `outputs/`
  - Final optimizer and Monte Carlo pipeline outputs.
- `adps_lectures/`
  - Python notebooks covering optimization, Cython, concurrency, and GPU techniques used as reference for the optimized pipeline.
- `Info_md's/`
  - Supporting markdown reference files for the project.
- `requirements.txt`
  - Pinned Python dependencies for the repo-local environment.
- `mc_core.pyx`
  - Cython source for the Monte Carlo simulation inner loop.
- `setup_mc_cython.py`
  - Builds `mc_core.pyx` into a compiled `.so` extension in-place - creates a C script version vua Cython 
