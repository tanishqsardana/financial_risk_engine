from __future__ import annotations

import csv
import math
import time
from pathlib import Path

import numpy as np


BASE_DIR = Path(__file__).resolve().parent
REAL_DATA_DIR = BASE_DIR / "real_data"
OUTPUT_DIR = BASE_DIR / "covariance_experiments"
RNG = np.random.default_rng(1019)
TARGET_SIZES = [28, 56, 112, 224, 448, 896, 1792]
DTYPES = [np.float64, np.float32]
FACTOR_COLUMNS = [
    "delta_treasury_2y",
    "delta_treasury_10y",
    "delta_treasury_slope_10y_2y",
    "delta_corp_baa_aaa_spread",
]


def load_monthly_returns(path: Path) -> tuple[list[str], list[str], np.ndarray]:
    rows_by_month: dict[str, dict[str, float]] = {}
    asset_ids: set[str] = set()
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            month = row["month"]
            asset_id = row["asset_id"]
            value = float(row["monthly_return"])
            rows_by_month.setdefault(month, {})[asset_id] = value
            asset_ids.add(asset_id)

    months = sorted(rows_by_month)
    assets = sorted(asset_ids)
    matrix = np.array(
        [[rows_by_month[month][asset_id] for asset_id in assets] for month in months],
        dtype=np.float64,
    )
    return months, assets, matrix


def load_factor_matrix(path: Path, months: list[str]) -> np.ndarray:
    factor_rows: dict[str, dict[str, float]] = {}
    with path.open() as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            month = row["date"][:7]
            factor_rows[month] = {
                "treasury_2y_pct": float(row["treasury_2y_pct"]),
                "treasury_10y_pct": float(row["treasury_10y_pct"]),
                "treasury_slope_10y_2y_pct": float(row["treasury_slope_10y_2y_pct"]),
                "corp_baa_aaa_spread_pct": float(row["corp_baa_aaa_spread_pct"]),
            }

    aligned = [factor_rows[month] for month in months]
    t2 = np.array([row["treasury_2y_pct"] for row in aligned], dtype=np.float64)
    t10 = np.array([row["treasury_10y_pct"] for row in aligned], dtype=np.float64)
    slope = np.array([row["treasury_slope_10y_2y_pct"] for row in aligned], dtype=np.float64)
    spread = np.array([row["corp_baa_aaa_spread_pct"] for row in aligned], dtype=np.float64)

    factors = np.column_stack(
        [
            np.diff(t2, prepend=t2[0]) / 100.0,
            np.diff(t10, prepend=t10[0]) / 100.0,
            np.diff(slope, prepend=slope[0]) / 100.0,
            np.diff(spread, prepend=spread[0]) / 100.0,
        ]
    )
    return factors


def expand_return_panel(base_returns: np.ndarray, target_size: int) -> np.ndarray:
    periods, base_assets = base_returns.shape
    if target_size == base_assets:
        return base_returns.copy()

    expanded = np.zeros((periods, target_size), dtype=np.float64)
    column_stds = np.std(base_returns, axis=0, ddof=1)
    for j in range(target_size):
        source_idx = j % base_assets
        secondary_idx = (j * 7 + 3) % base_assets
        scale = RNG.uniform(0.92, 1.08)
        mix = RNG.uniform(0.0, 0.18)
        noise_scale = max(1e-5, column_stds[source_idx] * RNG.uniform(0.04, 0.08))
        noise = RNG.normal(loc=0.0, scale=noise_scale, size=periods)
        expanded[:, j] = (
            scale * base_returns[:, source_idx]
            + mix * base_returns[:, secondary_idx]
            + noise
        )
    return expanded


def sample_covariance(returns: np.ndarray) -> np.ndarray:
    centered = returns - returns.mean(axis=0, keepdims=True)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        return centered.T @ centered / (returns.shape[0] - 1)


def factor_model_covariance(returns: np.ndarray, factors: np.ndarray) -> np.ndarray:
    x = returns - returns.mean(axis=0, keepdims=True)
    f = factors - factors.mean(axis=0, keepdims=True)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        ftf_inv = np.linalg.pinv(f.T @ f)
        betas = ftf_inv @ f.T @ x
        residuals = x - f @ betas
        factor_cov = f.T @ f / (f.shape[0] - 1)
    residual_var = np.sum(residuals * residuals, axis=0) / (residuals.shape[0] - 1)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        return betas.T @ factor_cov @ betas + np.diag(residual_var)


def benchmark(function, returns: np.ndarray, factors: np.ndarray | None, repeats: int) -> tuple[np.ndarray, float]:
    cov = None
    start = time.perf_counter()
    for _ in range(repeats):
        cov = function(returns) if factors is None else function(returns, factors)
    elapsed = (time.perf_counter() - start) / repeats
    assert cov is not None
    return cov, elapsed


def bytes_to_mb(value: int) -> float:
    return value / (1024.0 * 1024.0)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_best_configs(rows: list[dict[str, object]]) -> list[str]:
    lines: list[str] = []
    grouped: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(int(row["n_assets"]), []).append(row)

    for size in sorted(grouped):
        configs = grouped[size]
        sample64 = next(row for row in configs if row["method"] == "sample" and row["dtype"] == "float64")
        factor64 = next(row for row in configs if row["method"] == "factor" and row["dtype"] == "float64")
        sample32 = next(row for row in configs if row["method"] == "sample" and row["dtype"] == "float32")
        lines.append(
            (
                f"- N={size}: sample float64 {float(sample64['runtime_ms']):.4f} ms, "
                f"factor float64 {float(factor64['runtime_ms']):.4f} ms, "
                f"sample float32 matrix memory {float(sample32['covariance_matrix_mb']):.4f} MB, "
                f"factor-vs-sample relative error {float(factor64['relative_error_vs_sample64']):.4f}"
            )
        )
    return lines


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    months, base_assets, base_returns = load_monthly_returns(
        REAL_DATA_DIR / "real_bond_monthly_returns.csv"
    )
    factor_matrix = load_factor_matrix(REAL_DATA_DIR / "real_bond_factors_monthly.csv", months)

    benchmark_rows: list[dict[str, object]] = []
    matrix_rows: list[dict[str, object]] = []

    for target_size in TARGET_SIZES:
        expanded_returns = expand_return_panel(base_returns, target_size)
        matrix_rows.append(
            {
                "n_assets": target_size,
                "n_periods": expanded_returns.shape[0],
                "base_assets_used": len(base_assets),
                "construction": "real_panel_derived_expansion" if target_size > len(base_assets) else "observed_real_assets",
            }
        )

        baseline_cov64, _ = benchmark(sample_covariance, expanded_returns.astype(np.float64), None, repeats=5)

        for dtype in DTYPES:
            dtype_name = "float64" if dtype == np.float64 else "float32"
            typed_returns = expanded_returns.astype(dtype)
            typed_factors = factor_matrix.astype(dtype)
            repeats = 20 if target_size <= 224 else 8

            sample_cov, sample_runtime = benchmark(
                sample_covariance, typed_returns, None, repeats=repeats
            )
            factor_cov, factor_runtime = benchmark(
                factor_model_covariance, typed_returns, typed_factors, repeats=repeats
            )

            sample_rel_error = float(
                np.linalg.norm(sample_cov.astype(np.float64) - baseline_cov64, ord="fro")
                / max(np.linalg.norm(baseline_cov64, ord="fro"), 1e-12)
            )
            factor_rel_error = float(
                np.linalg.norm(factor_cov.astype(np.float64) - baseline_cov64, ord="fro")
                / max(np.linalg.norm(baseline_cov64, ord="fro"), 1e-12)
            )

            benchmark_rows.extend(
                [
                    {
                        "n_assets": target_size,
                        "n_periods": typed_returns.shape[0],
                        "method": "sample",
                        "dtype": dtype_name,
                        "runtime_ms": round(sample_runtime * 1000.0, 6),
                        "return_panel_mb": round(bytes_to_mb(typed_returns.nbytes), 6),
                        "covariance_matrix_mb": round(
                            bytes_to_mb(sample_cov.nbytes), 6
                        ),
                        "relative_error_vs_sample64": round(sample_rel_error, 8),
                    },
                    {
                        "n_assets": target_size,
                        "n_periods": typed_returns.shape[0],
                        "method": "factor",
                        "dtype": dtype_name,
                        "runtime_ms": round(factor_runtime * 1000.0, 6),
                        "return_panel_mb": round(bytes_to_mb(typed_returns.nbytes), 6),
                        "covariance_matrix_mb": round(
                            bytes_to_mb(factor_cov.nbytes), 6
                        ),
                        "relative_error_vs_sample64": round(factor_rel_error, 8),
                    },
                ]
            )

    write_csv(
        OUTPUT_DIR / "covariance_benchmark_results.csv",
        [
            "n_assets",
            "n_periods",
            "method",
            "dtype",
            "runtime_ms",
            "return_panel_mb",
            "covariance_matrix_mb",
            "relative_error_vs_sample64",
        ],
        benchmark_rows,
    )
    write_csv(
        OUTPUT_DIR / "covariance_experiment_sizes.csv",
        ["n_assets", "n_periods", "base_assets_used", "construction"],
        matrix_rows,
    )

    summary_lines = [
        "# Covariance Matrix Experiments",
        "",
        "These experiments benchmark covariance matrix construction on the real monthly bond return panel in "
        "`real_data/real_bond_monthly_returns.csv`.",
        "",
        "## Methodology",
        "",
        "- Base data: 28 real bond assets across 120 monthly observations from 2016-01 through 2025-12.",
        "- Scaled universes: for N > 28, the script expands the observed real panel by cloning real asset return series with small noise and cross-asset mixing. This preserves the real-data backbone while making large-N timing experiments possible.",
        "- Sample covariance: direct centered matrix multiplication.",
        "- Factor covariance: four-factor model using monthly changes in 2Y Treasury, 10Y Treasury, 10Y-2Y slope, and BAA-AAA spread.",
        "- Numeric precision: `float64` and `float32` are both benchmarked.",
        "",
        "## Selected Results",
        "",
        *summarize_best_configs(benchmark_rows),
        "",
        "## Output Files",
        "",
        "- `covariance_experiments/covariance_benchmark_results.csv`",
        "- `covariance_experiments/covariance_experiment_sizes.csv`",
        "",
        "## Factor Columns",
        "",
        *[f"- `{column}`" for column in FACTOR_COLUMNS],
    ]
    (OUTPUT_DIR / "covariance_experiment_summary.md").write_text("\n".join(summary_lines) + "\n")


if __name__ == "__main__":
    main()
