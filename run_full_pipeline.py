from __future__ import annotations

from pathlib import Path

import pandas as pd

from factor_covariance_benchmark import benchmark_covariance_methods
from mip_bond_optimizer import run_all_scenarios
from monte_carlo_engine import run_monte_carlo
from solver_comparison import run_solver_comparison
from stress_testing_engine import run_stress_tests


REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "outputs"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bond_universe = pd.read_csv(DATA_DIR / "synthetic_bond_universe.csv")
    cov_matrix = pd.read_csv(DATA_DIR / "synthetic_covariance_matrix.csv", index_col=0)

    scenario_results = run_all_scenarios(bond_universe, cov_matrix=cov_matrix)
    summary_rows: list[dict[str, object]] = []

    for scenario_id, result in scenario_results.items():
        if result.get("status") != "Optimal":
            continue

        portfolio_df = result["portfolio_df"]
        if portfolio_df.empty:
            continue

        portfolio_path = OUTPUT_DIR / f"portfolio_scenario_{scenario_id}.csv"
        portfolio_df.to_csv(portfolio_path, index=False)

        mc_result = run_monte_carlo(portfolio_df, cov_matrix)
        mc_returns_df = mc_result["simulated_returns"]
        mc_metrics_df = mc_result["metrics"]

        mc_returns_path = OUTPUT_DIR / f"mc_returns_scenario_{scenario_id}.csv"
        mc_metrics_path = OUTPUT_DIR / f"mc_metrics_scenario_{scenario_id}.csv"
        mc_returns_df.to_csv(mc_returns_path, index=False)
        mc_metrics_df.to_csv(mc_metrics_path, index=False)

        stress_result = run_stress_tests(portfolio_df, cov_matrix)
        stress_metrics_df = pd.concat(stress_result.values(), ignore_index=True)
        stress_metrics_df.to_csv(
            OUTPUT_DIR / f"stress_metrics_scenario_{scenario_id}.csv", index=False
        )

        summary_metrics = dict(result["summary_metrics"])
        summary_rows.append(
            {
                "scenario_id": scenario_id,
                "scenario_name": result["scenario_name"],
                "status": result["status"],
                "objective_value": result["objective_value"],
                "solve_time_seconds": result["solve_time_seconds"],
                **summary_metrics,
            }
        )

        print(f"Scenario {scenario_id}: {result['scenario_name']}")
        print(f"  Solve time: {result['solve_time_seconds']:.5f} seconds")
        print(f"  Portfolio variance: {summary_metrics['portfolio_variance']:.8f}")
        print(f"  Portfolio volatility: {summary_metrics['portfolio_volatility']:.8f}")
        for metric_row in mc_metrics_df.to_dict(orient="records"):
            confidence_level = int(metric_row["confidence_level"] * 100)
            print(
                f"  VaR {confidence_level}%: {metric_row['var']:.6f} | "
                f"CVaR {confidence_level}%: {metric_row['cvar']:.6f}"
            )
        print(f"  Stress scenarios saved: {sorted(stress_result)}")
        print()

    if summary_rows:
        pd.DataFrame(summary_rows).to_csv(OUTPUT_DIR / "scenario_summary.csv", index=False)

    solver_comparison_df = run_solver_comparison(bond_universe, cov_matrix)
    solver_comparison_df.to_csv(OUTPUT_DIR / "solver_comparison.csv", index=False)
    print("Solver comparison")
    print(solver_comparison_df.to_string(index=False))
    print()

    factor_benchmark_df = benchmark_covariance_methods(
        bond_universe=bond_universe,
        return_history_path=DATA_DIR / "synthetic_bond_history.csv",
    )
    factor_benchmark_df.to_csv(OUTPUT_DIR / "factor_covariance_benchmark.csv", index=False)
    print("Factor covariance benchmark")
    print(factor_benchmark_df.to_string(index=False))


if __name__ == "__main__":
    main()
