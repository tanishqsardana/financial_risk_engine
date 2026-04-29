from __future__ import annotations

import time

import numpy as np
import pandas as pd


def prepare_mean_variance_inputs(
    bond_universe: pd.DataFrame, cov_matrix: pd.DataFrame, max_assets: int = 250
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    available_ids = set(cov_matrix.index.astype(str))
    bond_df = bond_universe.copy()
    bond_df["bond_id"] = bond_df["bond_id"].astype(str)
    bond_df = bond_df[bond_df["bond_id"].isin(available_ids)].copy()
    bond_df = bond_df.sort_values(
        ["rating_bucket", "liquidity_score", "expected_annual_return_pct"],
        ascending=[True, False, False],
    ).head(max_assets)
    sigma = cov_matrix.loc[bond_df["bond_id"], bond_df["bond_id"]].copy()
    mu = bond_df["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0
    return bond_df.reset_index(drop=True), mu, sigma


def _regularize_covariance(cov_matrix: pd.DataFrame | np.ndarray) -> np.ndarray:
    sigma = np.asarray(cov_matrix, dtype=float)
    sigma = (sigma + sigma.T) / 2.0
    eigvals, eigvecs = np.linalg.eigh(sigma)
    eigvals = np.clip(eigvals, 1e-8, None)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        return eigvecs @ np.diag(eigvals) @ eigvecs.T


def solve_cvxpy_mean_variance(
    bond_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    solver_name: str = "OSQP",
    risk_aversion: float = 0.1,
) -> dict[str, object]:
    try:
        import cvxpy as cp
    except Exception as exc:
        return {
            "solver": f"cvxpy_{solver_name}",
            "formulation": "continuous_mean_variance_relaxation",
            "status": f"error: {exc}",
            "objective_value": None,
            "solve_time_seconds": None,
            "nonzero_weight_count": None,
        }

    mu = bond_df["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0
    sigma = _regularize_covariance(cov_matrix)
    n_assets = len(mu)
    weights = cp.Variable(n_assets)
    objective = cp.Maximize(
        mu @ weights - risk_aversion * cp.quad_form(weights, cp.psd_wrap(sigma))
    )
    constraints = [cp.sum(weights) == 1, weights >= 0]
    problem = cp.Problem(objective, constraints)

    start_time = time.perf_counter()
    try:
        problem.solve(solver=getattr(cp, solver_name), verbose=False)
        solve_time = time.perf_counter() - start_time
        weight_values = np.asarray(weights.value).reshape(-1) if weights.value is not None else None
        return {
            "solver": f"cvxpy_{solver_name}",
            "formulation": "continuous_mean_variance_relaxation",
            "status": problem.status,
            "objective_value": float(problem.value) if problem.value is not None else None,
            "solve_time_seconds": solve_time,
            "nonzero_weight_count": int(np.sum(weight_values > 1e-6)) if weight_values is not None else None,
        }
    except Exception as exc:
        return {
            "solver": f"cvxpy_{solver_name}",
            "formulation": "continuous_mean_variance_relaxation",
            "status": f"error: {exc}",
            "objective_value": None,
            "solve_time_seconds": time.perf_counter() - start_time,
            "nonzero_weight_count": None,
        }


def solve_scipy_slsqp_mean_variance(
    bond_df: pd.DataFrame, cov_matrix: pd.DataFrame, risk_aversion: float = 0.1
) -> dict[str, object]:
    try:
        from scipy.optimize import minimize
    except Exception as exc:
        return {
            "solver": "scipy_slsqp",
            "formulation": "continuous_mean_variance_relaxation",
            "status": f"error: {exc}",
            "objective_value": None,
            "solve_time_seconds": None,
            "nonzero_weight_count": None,
        }

    mu = bond_df["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0
    sigma = _regularize_covariance(cov_matrix)
    n_assets = len(mu)

    def objective(weights: np.ndarray) -> float:
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            return -float(mu @ weights - risk_aversion * weights.T @ sigma @ weights)

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0)] * n_assets
    x0 = np.full(n_assets, 1.0 / n_assets)

    start_time = time.perf_counter()
    try:
        result = minimize(
            objective,
            x0=x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        solve_time = time.perf_counter() - start_time
        return {
            "solver": "scipy_slsqp",
            "formulation": "continuous_mean_variance_relaxation",
            "status": "optimal" if result.success else result.message,
            "objective_value": -float(result.fun) if result.success else None,
            "solve_time_seconds": solve_time,
            "nonzero_weight_count": int(np.sum(result.x > 1e-6)) if result.success else None,
        }
    except Exception as exc:
        return {
            "solver": "scipy_slsqp",
            "formulation": "continuous_mean_variance_relaxation",
            "status": f"error: {exc}",
            "objective_value": None,
            "solve_time_seconds": time.perf_counter() - start_time,
            "nonzero_weight_count": None,
        }


def run_solver_comparison(
    bond_universe: pd.DataFrame, cov_matrix: pd.DataFrame
) -> pd.DataFrame:
    bond_df, _, sigma = prepare_mean_variance_inputs(bond_universe, cov_matrix)
    rows = [
        solve_cvxpy_mean_variance(bond_df, sigma, solver_name="OSQP"),
        solve_scipy_slsqp_mean_variance(bond_df, sigma),
    ]
    result_df = pd.DataFrame(rows)
    result_df.insert(0, "n_assets", len(bond_df))
    return result_df
