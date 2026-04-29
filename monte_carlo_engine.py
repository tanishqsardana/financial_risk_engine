from __future__ import annotations

import numpy as np
import pandas as pd


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
    expected_returns = (
        selected["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0
    )
    sigma = cov_matrix.loc[bond_ids, bond_ids].to_numpy(dtype=float)
    sigma = (sigma + sigma.T) / 2.0

    rng = np.random.default_rng(random_seed)
    simulated_asset_returns = rng.multivariate_normal(
        mean=expected_returns,
        cov=sigma,
        size=n_simulations,
    )
    return simulated_asset_returns @ weights


def compute_risk_metrics(
    simulated_returns: np.ndarray,
    confidence_levels: tuple[float, ...] = (0.95, 0.99),
) -> pd.DataFrame:
    simulated_returns = np.asarray(simulated_returns, dtype=float)
    if simulated_returns.size == 0:
        return pd.DataFrame(
            columns=[
                "confidence_level",
                "mean_return",
                "std_return",
                "min_return",
                "max_return",
                "var",
                "cvar",
            ]
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
        rows.append(
            {
                "confidence_level": confidence_level,
                "mean_return": mean_return,
                "std_return": std_return,
                "min_return": min_return,
                "max_return": max_return,
                "var": var_value,
                "cvar": cvar_value,
            }
        )

    return pd.DataFrame(rows)


def run_monte_carlo(
    portfolio_df: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    n_simulations: int = 10_000,
    random_seed: int = 42,
) -> dict[str, object]:
    simulated_returns = simulate_portfolio_returns(
        portfolio_df=portfolio_df,
        cov_matrix=cov_matrix,
        n_simulations=n_simulations,
        random_seed=random_seed,
    )
    metrics_df = compute_risk_metrics(simulated_returns)
    return {
        "simulated_returns": pd.DataFrame(
            {"simulated_portfolio_return": simulated_returns}
        ),
        "metrics": metrics_df,
    }
