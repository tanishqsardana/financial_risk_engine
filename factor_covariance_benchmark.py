from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "outputs"
FACTOR_COLUMNS = [
    "level_beta",
    "slope_beta",
    "spread_ig_beta",
    "spread_hy_beta",
    "muni_beta",
    "fx_beta",
]


def build_factor_covariance(
    bond_universe: pd.DataFrame,
    factor_cov: np.ndarray | pd.DataFrame | None = None,
    id_col: str = "bond_id",
) -> pd.DataFrame:
    beta_matrix = bond_universe[FACTOR_COLUMNS].to_numpy(dtype=float)
    n_factors = beta_matrix.shape[1]

    if factor_cov is None:
        factor_cov_matrix = np.eye(n_factors, dtype=float) * 0.0004
    else:
        factor_cov_matrix = np.asarray(factor_cov, dtype=float)

    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        systematic_cov = beta_matrix @ factor_cov_matrix @ beta_matrix.T
    total_variance = (bond_universe["annual_volatility_pct"].to_numpy(dtype=float) / 100.0) ** 2
    idiosyncratic_variance = np.clip(total_variance - np.diag(systematic_cov), 1e-8, None)
    covariance = systematic_cov + np.diag(idiosyncratic_variance)
    covariance = (covariance + covariance.T) / 2.0

    bond_ids = bond_universe[id_col].astype(str).tolist()
    return pd.DataFrame(covariance, index=bond_ids, columns=bond_ids)


def _load_sample_return_history(return_history_path: str | Path) -> pd.DataFrame | None:
    path = Path(return_history_path)
    if not path.exists() or path.stat().st_size == 0:
        return None

    history_df = pd.read_csv(path)
    required_cols = {"date", "bond_id", "monthly_total_return"}
    if required_cols.issubset(history_df.columns):
        pivot_df = history_df.pivot(
            index="date", columns="bond_id", values="monthly_total_return"
        )
        return pivot_df.sort_index(axis=1)

    if "bond_id" in history_df.columns:
        return history_df.set_index(history_df.columns[0])

    return None


def benchmark_covariance_methods(
    bond_universe: pd.DataFrame,
    return_history_path: str | Path | None = None,
    sizes: tuple[int, ...] = (100, 250, 500, 1000),
) -> pd.DataFrame:
    results: list[dict[str, object]] = []
    sample_history = (
        _load_sample_return_history(return_history_path) if return_history_path is not None else None
    )

    bond_df = bond_universe.copy()
    bond_df["bond_id"] = bond_df["bond_id"].astype(str)

    for size in sizes:
        if size > len(bond_df):
            continue

        subset_df = bond_df.head(size).copy()
        bond_ids = subset_df["bond_id"].tolist()

        start_time = time.perf_counter()
        factor_cov = build_factor_covariance(subset_df)
        factor_runtime = time.perf_counter() - start_time
        factor_memory_mb = factor_cov.memory_usage(index=True).sum() / (1024.0 * 1024.0)
        results.append(
            {
                "method": "factor_covariance",
                "status": "completed",
                "n_assets": size,
                "runtime_seconds": factor_runtime,
                "approx_memory_mb": factor_memory_mb,
            }
        )

        if sample_history is None:
            results.append(
                {
                    "method": "sample_covariance",
                    "status": "skipped: no return history",
                    "n_assets": size,
                    "runtime_seconds": None,
                    "approx_memory_mb": None,
                }
            )
            continue

        matching_ids = [bond_id for bond_id in bond_ids if bond_id in sample_history.columns]
        if len(matching_ids) < 2:
            results.append(
                {
                    "method": "sample_covariance",
                    "status": "skipped: insufficient matching history",
                    "n_assets": size,
                    "runtime_seconds": None,
                    "approx_memory_mb": None,
                }
            )
            continue

        sample_returns = sample_history[matching_ids].dropna(axis=0, how="any")
        if sample_returns.empty:
            results.append(
                {
                    "method": "sample_covariance",
                    "status": "skipped: empty matching history",
                    "n_assets": size,
                    "runtime_seconds": None,
                    "approx_memory_mb": None,
                }
            )
            continue

        start_time = time.perf_counter()
        sample_cov = sample_returns.cov()
        sample_runtime = time.perf_counter() - start_time
        sample_memory_mb = sample_cov.memory_usage(index=True).sum() / (1024.0 * 1024.0)
        results.append(
            {
                "method": "sample_covariance",
                "status": "completed",
                "n_assets": len(matching_ids),
                "runtime_seconds": sample_runtime,
                "approx_memory_mb": sample_memory_mb,
            }
        )

    return pd.DataFrame(results)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bond_universe = pd.read_csv(REPO_ROOT / "data" / "synthetic_bond_universe.csv")
    results_df = benchmark_covariance_methods(
        bond_universe=bond_universe,
        return_history_path=REPO_ROOT / "data" / "synthetic_bond_history.csv",
    )
    results_df.to_csv(OUTPUT_DIR / "factor_covariance_benchmark.csv", index=False)
    print(results_df.to_string(index=False))


if __name__ == "__main__":
    main()
