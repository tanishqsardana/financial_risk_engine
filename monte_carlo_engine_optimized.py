from __future__ import annotations

import os
from multiprocessing import Pool

import numpy as np
import pandas as pd

try:
    import mc_core
    _CYTHON_AVAILABLE = True
except ImportError:
    _CYTHON_AVAILABLE = False


def _regularize_covariance(cov_matrix: pd.DataFrame | np.ndarray) -> np.ndarray:
    sigma = np.asarray(cov_matrix, dtype=float)
    sigma = (sigma + sigma.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(sigma)
    eigvals = np.clip(eigvals, 1e-8, None)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        return eigvecs @ np.diag(eigvals) @ eigvecs.T # vectorized solution


def _cholesky_safe(sigma: np.ndarray) -> np.ndarray:
    try:
        return np.linalg.cholesky(sigma)
    except np.linalg.LinAlgError:
        sigma = _regularize_covariance(sigma)
        return np.linalg.cholesky(sigma)

"""Numpy baseline path (mirrors monte_carlo_engine.py exactly)."""
def simulate_portfolio_returns(
    portfolio_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 10_000,
    random_seed: int = 42,
) -> np.ndarray:
    if portfolio_df.empty:
        return np.array([], dtype=float)

    selected = portfolio_df.set_index("bond_id")
    bond_ids = selected.index.tolist()
    weights = selected["portfolio_weight"].to_numpy(dtype=float)
    expected_returns = selected["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0
    sigma = _regularize_covariance(cov_matrix.loc[bond_ids, bond_ids])

    rng = np.random.default_rng(random_seed)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        simulated_asset_returns = rng.multivariate_normal(
            mean=expected_returns, cov=sigma, size=n_simulations, check_valid="ignore"
        )
        return simulated_asset_returns @ weights

"""
# simulate_portfolio_returns_cython(): 
# utilizing Cython for portfolio simulation - faster runtime performance for intesive # of simulations 
"""
def simulate_portfolio_returns_cython(
    portfolio_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 10_000,
    random_seed: int = 42,
) -> np.ndarray:
    if portfolio_df.empty:
        return np.array([], dtype=float)
    if not _CYTHON_AVAILABLE:
        return simulate_portfolio_returns(portfolio_df, cov_matrix, n_simulations, random_seed)

    selected = portfolio_df.set_index("bond_id")
    bond_ids = selected.index.tolist()
    weights = selected["portfolio_weight"].to_numpy(dtype=float)
    expected_returns = selected["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0
    sigma = _regularize_covariance(cov_matrix.loc[bond_ids, bond_ids])
    L = _cholesky_safe(sigma)

    rng = np.random.default_rng(random_seed)
    z = np.ascontiguousarray(rng.standard_normal((n_simulations, len(bond_ids))), dtype=np.float64)

    return mc_core.simulate_returns_cython(
        np.ascontiguousarray(expected_returns, dtype=np.float64),
        np.ascontiguousarray(L, dtype=np.float64),
        np.ascontiguousarray(weights, dtype=np.float64),
        z,
    )


def _chunk_worker(args: tuple) -> np.ndarray:
    portfolio_df, cov_matrix, n_chunk, seed = args
    return simulate_portfolio_returns(portfolio_df, cov_matrix, n_chunk, seed)

"""
# simulate_portfolio_returns_parallel() 
# function splits simulations across CPU processes, then concatenates and returns the 
# total set of results.  
"""
def simulate_portfolio_returns_parallel(
    portfolio_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 10_000,
    random_seed: int = 42,
    n_workers: int | None = None,
) -> np.ndarray:
    if portfolio_df.empty:
        return np.array([], dtype=float)

    n_workers = n_workers or min(os.cpu_count() or 4, 8)
    chunk_size = n_simulations // n_workers
    remainder = n_simulations - chunk_size * n_workers
    seeds = [random_seed + i for i in range(n_workers)]
    chunks = [chunk_size + (1 if i < remainder else 0) for i in range(n_workers)]
    args = [(portfolio_df, cov_matrix, c, s) for c, s in zip(chunks, seeds)]

    with Pool(n_workers) as pool:
        results = pool.map(_chunk_worker, args)

    return np.concatenate(results)


def compute_risk_metrics(
    simulated_returns: np.ndarray,
    confidence_levels: tuple[float, ...] = (0.95, 0.99),
) -> pd.DataFrame:
    simulated_returns = np.asarray(simulated_returns, dtype=float)
    if simulated_returns.size == 0:
        return pd.DataFrame(
            columns=["confidence_level", "mean_return", "std_return",
                     "min_return", "max_return", "var", "cvar"]
        )

    mean_return = float(simulated_returns.mean())
    std_return = float(simulated_returns.std(ddof=1))
    min_return = float(simulated_returns.min())
    max_return = float(simulated_returns.max())

    rows = []
    for confidence_level in confidence_levels:
        tail_quantile = float(np.quantile(simulated_returns, 1.0 - confidence_level))
        tail_losses = simulated_returns[simulated_returns <= tail_quantile]
        var_value = -tail_quantile
        cvar_value = -float(tail_losses.mean()) if tail_losses.size else var_value
        rows.append({
            "confidence_level": confidence_level,
            "mean_return": mean_return,
            "std_return": std_return,
            "min_return": min_return,
            "max_return": max_return,
            "var": var_value,
            "cvar": cvar_value,
        })

    return pd.DataFrame(rows)


def run_monte_carlo(
    portfolio_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 10_000,
    random_seed: int = 42,
    use_parallel: bool = True,
    use_cython: bool = True,
) -> dict[str, object]:
    if use_cython and _CYTHON_AVAILABLE:
        simulated_returns = simulate_portfolio_returns_cython(
            portfolio_df, cov_matrix, n_simulations, random_seed
        )
    elif use_parallel:
        simulated_returns = simulate_portfolio_returns_parallel(
            portfolio_df, cov_matrix, n_simulations, random_seed
        )
    else:
        simulated_returns = simulate_portfolio_returns(
            portfolio_df, cov_matrix, n_simulations, random_seed
        )

    metrics_df = compute_risk_metrics(simulated_returns)
    return {
        "simulated_returns": pd.DataFrame({"simulated_portfolio_return": simulated_returns}),
        "metrics": metrics_df,
    }
