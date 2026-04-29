from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = REPO_ROOT / "outputs"
FACTOR_COLUMNS = [
    "level_beta", "slope_beta", "spread_ig_beta",
    "spread_hy_beta", "muni_beta", "fx_beta",
]

"""
# build_factor_covariance() 
# evaluate the covariance risk model for a bond portfolio from the entire bond universe (available bonds)
"""
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

"""
# loading sample return history for bond dataset
"""
def _load_sample_return_history(return_history_path: str | Path) -> pd.DataFrame | None:
    path = Path(return_history_path)
    if not path.exists() or path.stat().st_size == 0:
        return None
    history_df = pd.read_csv(path)
    required_cols = {"date", "bond_id", "monthly_total_return"}
    if required_cols.issubset(history_df.columns):
        pivot_df = history_df.pivot(index="date", columns="bond_id", values="monthly_total_return")
        return pivot_df.sort_index(axis=1)
    if "bond_id" in history_df.columns:
        return history_df.set_index(history_df.columns[0])
    return None

""" 
# benchmark_one_size():
# worker function - benchmark factor + sample covariance for a single asset count
"""
def _benchmark_worker(args: tuple) -> list[dict[str, object]]:
    size, bond_df_dict, sample_history_dict, has_history = args
    bond_df = pd.DataFrame(bond_df_dict)
    if size > len(bond_df):
        return []

    subset_df = bond_df.head(size).copy()
    bond_ids = subset_df["bond_id"].tolist()
    rows: list[dict[str, object]] = []

    t0 = time.perf_counter()
    factor_cov = build_factor_covariance(subset_df)
    factor_runtime = time.perf_counter() - t0
    factor_memory_mb = factor_cov.memory_usage(index=True).sum() / (1024.0 * 1024.0)
    rows.append({
        "method": "factor_covariance",
        "status": "completed",
        "n_assets": size,
        "runtime_seconds": factor_runtime,
        "approx_memory_mb": factor_memory_mb,
    })

    if not has_history:
        rows.append({
            "method": "sample_covariance",
            "status": "skipped: no return history",
            "n_assets": size,
            "runtime_seconds": None,
            "approx_memory_mb": None,
        })
        return rows

    sample_history = pd.DataFrame(sample_history_dict)
    matching_ids = [bid for bid in bond_ids if bid in sample_history.columns]
    if len(matching_ids) < 2:
        rows.append({
            "method": "sample_covariance",
            "status": "skipped: insufficient matching history",
            "n_assets": size, "runtime_seconds": None, "approx_memory_mb": None,
        })
        return rows

    sample_returns = sample_history[matching_ids].dropna(axis=0, how="any")
    if sample_returns.empty:
        rows.append({
            "method": "sample_covariance",
            "status": "skipped: empty matching history",
            "n_assets": size, "runtime_seconds": None, "approx_memory_mb": None,
        })
        return rows

    t0 = time.perf_counter()
    sample_cov = sample_returns.cov()
    sample_runtime = time.perf_counter() - t0
    sample_memory_mb = sample_cov.memory_usage(index=True).sum() / (1024.0 * 1024.0)
    rows.append({
        "method": "sample_covariance",
        "status": "completed",
        "n_assets": len(matching_ids),
        "runtime_seconds": sample_runtime,
        "approx_memory_mb": sample_memory_mb,
    })
    return rows

""" 
# benchmark_covariance_methods()
# uses benchmark worker function for concurrent parallel processing covariance matrix 
"""
def benchmark_covariance_methods(
    bond_universe: pd.DataFrame,
    return_history_path: str | Path | None = None,
    sizes: tuple[int, ...] = (100, 250, 500, 1000),
) -> pd.DataFrame:
    sample_history = (
        _load_sample_return_history(return_history_path)
        if return_history_path is not None else None
    )

    bond_df = bond_universe.copy() # creating bond dataframe
    bond_df["bond_id"] = bond_df["bond_id"].astype(str)
    bond_df_dict = bond_df.to_dict(orient="list")
    sample_history_dict = sample_history.to_dict(orient="list") if sample_history is not None else {}
    has_history = sample_history is not None

    valid_sizes = [s for s in sizes if s <= len(bond_df)]
    args = [(s, bond_df_dict, sample_history_dict, has_history) for s in valid_sizes]

    # utlize parallel processing for calculating covariance benchmark 
    all_rows: list[dict[str, object]] = []
    with ProcessPoolExecutor(max_workers=min(len(args), 4)) as executor:
        futures = {executor.submit(_benchmark_worker, a): a[0] for a in args}
        for fut in as_completed(futures):
            all_rows.extend(fut.result())

    return pd.DataFrame(all_rows)

"""
# function to run script 
"""
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
