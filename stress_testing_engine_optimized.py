from __future__ import annotations

import os
from multiprocessing import Pool

import pandas as pd

from monte_carlo_engine_optimized import run_monte_carlo


def build_stress_covariance(
    cov_matrix: pd.DataFrame, stress_multiplier: float = 1.5
) -> pd.DataFrame:
    stressed = cov_matrix.astype(float) * float(stress_multiplier)
    stressed = (stressed + stressed.T) / 2.0
    stressed.index = cov_matrix.index
    stressed.columns = cov_matrix.columns
    return stressed


def build_return_shock_portfolio(
    portfolio_df: pd.DataFrame, return_shock: float = -0.01
) -> pd.DataFrame:
    stressed_portfolio = portfolio_df.copy()
    stressed_portfolio["expected_annual_return_pct"] = (
        stressed_portfolio["expected_annual_return_pct"] + return_shock * 100.0
    )
    return stressed_portfolio


def _run_scenario(args: tuple) -> tuple[str, pd.DataFrame]:
    scenario_name, scenario_portfolio, scenario_cov, n_simulations, random_seed = args
    mc_result = run_monte_carlo(
        scenario_portfolio,
        scenario_cov,
        n_simulations=n_simulations,
        random_seed=random_seed,
    )
    metrics_df = mc_result["metrics"].copy()
    metrics_df.insert(0, "scenario", scenario_name)
    return scenario_name, metrics_df


def run_stress_tests(
    portfolio_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 10_000,
    random_seed: int = 42,
    n_workers: int | None = None,
) -> dict[str, pd.DataFrame]:
    stressed_cov = build_stress_covariance(cov_matrix)
    shocked_portfolio = build_return_shock_portfolio(portfolio_df)

    scenario_inputs = {
        "baseline": (portfolio_df, cov_matrix),
        "covariance_stress": (portfolio_df, stressed_cov),
        "return_shock": (shocked_portfolio, cov_matrix),
        "combined_stress": (shocked_portfolio, stressed_cov),
    }

    args = [
        (name, port, cov, n_simulations, random_seed)
        for name, (port, cov) in scenario_inputs.items()
    ]

    n_workers = n_workers or min(os.cpu_count() or 4, len(args))
    with Pool(n_workers) as pool:
        paired = pool.map(_run_scenario, args)

    return {name: df for name, df in paired}
