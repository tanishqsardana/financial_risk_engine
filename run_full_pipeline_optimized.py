"""
This script is the optimized pipeline. Each technique added to the optimized 
pipeline is timed and compared against the baseline in run_full_pipeline.py.  

Techniques added to optimized pipeline:
- T1: Vectorized risk eval - numpy int-index covariance slicing
- T2: Parallel MIP scenarios - multiprocessing.Pool, 1 worker/scenario
- T3: Cython Monte Carlo Simulation - mc_core.pyx typed inner loop, n=100k
- T4  Multiprocessing MC - Pool chunks, n=100k
- T5  Parallel stress tests - Pool over 4 stress scenarios, n=100k
- T6  Parallel solver comparison - ThreadPoolExecutor
- T7  Parallel cov benchmark - ProcessPoolExecutor, avg over 5 reps

Prints a single summary DataFrame at the end with individualized and overall speedup results. 
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

# baseline imports
from factor_covariance_benchmark import benchmark_covariance_methods as bm_baseline
from mip_bond_optimizer import (
    eval_portfolio_risk as eval_risk_baseline,
    run_all_scenarios as scenarios_baseline,
)
from monte_carlo_engine import run_monte_carlo as mc_baseline
from solver_comparison import run_solver_comparison as solver_cmp_baseline
from stress_testing_engine import run_stress_tests as stress_baseline

# optimized imports
from factor_covariance_benchmark_optimized import (
    benchmark_covariance_methods as bm_optimized,
)
from mip_bond_optimizer_optimized import (
    eval_portfolio_risk_vectorized,
    run_all_scenarios_parallel,
)
from monte_carlo_engine_optimized import (
    _CYTHON_AVAILABLE,
    run_monte_carlo as mc_optimized,
    simulate_portfolio_returns,
    simulate_portfolio_returns_cython,
    simulate_portfolio_returns_parallel,
)
from solver_comparison_optimized import run_solver_comparison as solver_cmp_optimized
from stress_testing_engine_optimized import run_stress_tests as stress_optimized


REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "outputs"

N_MC = 100_000  # simulation count used for T3/T4/T5 benchmarks
N_BM_REPS = 5   # repetitions for T7 averaging


def _time(fn, *args, **kwargs) -> tuple[object, float]:
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - t0


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bond_universe = pd.read_csv(DATA_DIR / "synthetic_bond_universe.csv")
    cov_matrix = pd.read_csv(DATA_DIR / "synthetic_covariance_matrix.csv", index_col=0)
    return_history_path = DATA_DIR / "synthetic_bond_history.csv"

    cov_np = cov_matrix.to_numpy(dtype=float)
    id_to_idx = {bid: i for i, bid in enumerate(cov_matrix.index.astype(str))}

    rows: list[dict[str, object]] = []

    # T1: Vectorized risk eval
    scenario_results_base = scenarios_baseline(bond_universe, cov_matrix=cov_matrix)
    first_optimal = next(
        (r for r in scenario_results_base.values()
         if r.get("status") == "Optimal" and not r["portfolio_df"].empty),
        None,
    )
    if first_optimal is not None:
        pf = first_optimal["portfolio_df"]
        _, tb = _time(eval_risk_baseline, pf, cov_matrix)
        _, to = _time(eval_portfolio_risk_vectorized, pf, cov_np, id_to_idx)
        rows.append({"technique": "T1  Vectorized risk eval", "baseline_s": tb, "optimized_s": to})

    # T2: parallel MIP scenarios
    _, tb = _time(scenarios_baseline, bond_universe, cov_matrix=cov_matrix)
    scenario_results_opt, to = _time(run_all_scenarios_parallel, bond_universe, cov_matrix=cov_matrix)
    rows.append({"technique": "T2  Parallel MIP scenarios", "baseline_s": tb, "optimized_s": to})

    ref_portfolio = next(
        (r["portfolio_df"] for r in scenario_results_opt.values()
         if r.get("status") == "Optimal" and not r["portfolio_df"].empty),
        None,
    )

    # T3: Cython MC 
    if ref_portfolio is not None:
        if _CYTHON_AVAILABLE:
            simulate_portfolio_returns_cython(ref_portfolio, cov_matrix, 1_000)  # warm-up
            _, tb = _time(simulate_portfolio_returns, ref_portfolio, cov_matrix, N_MC)
            _, to = _time(simulate_portfolio_returns_cython, ref_portfolio, cov_matrix, N_MC)
        else:
            _, tb = _time(simulate_portfolio_returns, ref_portfolio, cov_matrix, N_MC)
            to = tb
        rows.append({"technique": f"T3  Cython MC (n={N_MC:,})", "baseline_s": tb, "optimized_s": to})

    # T4: multiprocessing MC (n=N_MC) 
    if ref_portfolio is not None:
        _, tb = _time(simulate_portfolio_returns, ref_portfolio, cov_matrix, N_MC)
        _, to = _time(simulate_portfolio_returns_parallel, ref_portfolio, cov_matrix, N_MC)
        rows.append({"technique": f"T4  Multiprocessing MC (n={N_MC:,})", "baseline_s": tb, "optimized_s": to})

    # T5: parallel stress tests (n=N_MC)
    if ref_portfolio is not None:
        _, tb = _time(stress_baseline, ref_portfolio, cov_matrix, n_simulations=N_MC)
        _, to = _time(stress_optimized, ref_portfolio, cov_matrix, n_simulations=N_MC)
        rows.append({"technique": f"T5  Parallel stress tests (n={N_MC:,})", "baseline_s": tb, "optimized_s": to})

    # T6: parallel solver comparison 
    _, tb = _time(solver_cmp_baseline, bond_universe, cov_matrix)
    solver_df_opt, to = _time(solver_cmp_optimized, bond_universe, cov_matrix)
    rows.append({"technique": "T6  Parallel solver comparison", "baseline_s": tb, "optimized_s": to})

    # T7: parallel covariance benchmark 
    bm_sizes = (100, 250, 500, 1000)
    tb_total, to_total = 0.0, 0.0
    for _ in range(N_BM_REPS):
        _, dt = _time(bm_baseline, bond_universe=bond_universe,
                      return_history_path=return_history_path, sizes=bm_sizes)
        tb_total += dt
    for _ in range(N_BM_REPS):
        _, dt = _time(bm_optimized, bond_universe=bond_universe,
                      return_history_path=return_history_path, sizes=bm_sizes)
        to_total += dt
    rows.append({
        "technique": f"T7  Parallel cov benchmark (avg/{N_BM_REPS})",
        "baseline_s": tb_total / N_BM_REPS,
        "optimized_s": to_total / N_BM_REPS,
    })

    # Full pipeline end-to-end 
    t0 = time.perf_counter()
    base_results2 = scenarios_baseline(bond_universe, cov_matrix=cov_matrix)
    for r in base_results2.values():
        if r.get("status") != "Optimal" or r["portfolio_df"].empty:
            continue
        mc_baseline(r["portfolio_df"], cov_matrix)
        stress_baseline(r["portfolio_df"], cov_matrix)
    solver_cmp_baseline(bond_universe, cov_matrix)
    bm_baseline(bond_universe=bond_universe, return_history_path=return_history_path)
    t_full_base = time.perf_counter() - t0

    t0 = time.perf_counter()
    for scenario_id, result in scenario_results_opt.items():
        if result.get("status") != "Optimal" or result["portfolio_df"].empty:
            continue
        portfolio_df = result["portfolio_df"]
        portfolio_df.to_csv(OUTPUT_DIR / f"portfolio_scenario_{scenario_id}.csv", index=False)
        mc_result = mc_optimized(portfolio_df, cov_matrix)
        mc_result["simulated_returns"].to_csv(
            OUTPUT_DIR / f"mc_returns_scenario_{scenario_id}.csv", index=False)
        mc_result["metrics"].to_csv(
            OUTPUT_DIR / f"mc_metrics_scenario_{scenario_id}.csv", index=False)
        stress_result = stress_optimized(portfolio_df, cov_matrix)
        pd.concat(stress_result.values(), ignore_index=True).to_csv(
            OUTPUT_DIR / f"stress_metrics_scenario_{scenario_id}.csv", index=False)
    solver_df_opt.to_csv(OUTPUT_DIR / "solver_comparison_optimized.csv", index=False)
    bm_df_opt = bm_optimized(bond_universe=bond_universe, return_history_path=return_history_path)
    bm_df_opt.to_csv(OUTPUT_DIR / "factor_covariance_benchmark_optimized.csv", index=False)
    t_full_opt = time.perf_counter() - t0

    rows.append({"technique": "TOTAL PIPELINE", "baseline_s": t_full_base, "optimized_s": t_full_opt})

    # Summary DataFrame
    summary = pd.DataFrame(rows)
    summary["speedup"] = (summary["baseline_s"] / summary["optimized_s"]).round(2)
    summary["baseline_s"] = summary["baseline_s"].round(4)
    summary["optimized_s"] = summary["optimized_s"].round(4)
    summary.columns = ["Technique", "Baseline (s)", "Optimized (s)", "Speedup"]

    print("\n" + summary.to_string(index=False))
    print()

if __name__ == "__main__":
    main()
