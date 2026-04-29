from __future__ import annotations

import os
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from pyomo.environ import (
    ConcreteModel,
    Constraint,
    NonNegativeIntegers,
    Objective,
    Param,
    Set,
    SolverFactory,
    SolverStatus,
    TerminationCondition,
    Var,
    maximize,
    value,
)


DATA_DIR = Path(__file__).resolve().parent / "data"

"""
# dictionaries for all 7 bond scenarios 
"""
CONSTRAINTS = {
    1: dict(
        name="Portfolio 1 — ~$50M target value, medium time horizon",
        fv_min=50_000_000, fv_max=50_500_000, liq_min=0.85, mat_max=20,
        ret_min=0.03, aaa_min=0.60, bbb_bb_max=0.10, vol_max=0.05,
    ),
    2: dict(
        name="Portfolio 2 — ~$20M target value, short time horizon, risk-averse",
        fv_min=20_000_000, fv_max=20_500_000, liq_min=0.95, mat_max=10,
        ret_min=0.03, aaa_min=0.80, bbb_bb_max=0.05, vol_max=0.02,
    ),
    3: dict(
        name="Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk",
        fv_min=100_000_000, fv_max=101_500_000, liq_min=0.70, mat_max=30,
        ret_min=0.03, aaa_min=0.80, bbb_bb_max=0.05, vol_max=0.05,
    ),
    4: dict(
        name="Portfolio 4 — ~$20M target value, short time horizon, risk-averse",
        fv_min=20_000_000, fv_max=20_500_000, liq_min=0.95, mat_max=10,
        ret_min=0.01, aaa_min=0.90, bbb_bb_max=0.03, vol_max=0.03,
    ),
    5: dict(
        name="Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile",
        fv_min=500_000_000, fv_max=505_000_000, liq_min=0.85, mat_max=20,
        ret_min=0.03, aaa_min=0.60, bbb_bb_max=0.10, vol_max=0.03,
    ),
    6: dict(
        name="Portfolio 6 — ~$75M target value, balanced risk, longer time horizon",
        fv_min=75_000_000, fv_max=76_000_000, liq_min=0.75, mat_max=25,
        ret_min=0.035, aaa_min=0.70, bbb_bb_max=0.08, vol_max=0.04,
    ),
    7: dict(
        name="Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon",
        fv_min=200_000_000, fv_max=202_000_000, liq_min=0.80, mat_max=15,
        ret_min=0.025, aaa_min=0.65, bbb_bb_max=0.12, vol_max=0.06,
    ),
}

"""
# Pre-cast all per-bond numeric attributes to numpy arrays and build an
# integer index map so downstream covariance slicing avoids pandas .loc.
"""
def _precompute_universe_arrays(bond_universe: pd.DataFrame) -> dict[str, object]:
    bu = bond_universe.copy()
    bu["bond_id"] = bu["bond_id"].astype(str)
    bond_ids = bu["bond_id"].tolist()
    id_to_idx: dict[str, int] = {bid: i for i, bid in enumerate(bond_ids)}

    return {
        "bond_ids": bond_ids,
        "id_to_idx": id_to_idx,
        "min_inc": bu["minimum_increment"].to_numpy(dtype=float),
        "exp_ret": bu["expected_annual_return_pct"].to_numpy(dtype=float) / 100.0,
        "liq_score": bu["liquidity_score"].to_numpy(dtype=float),
        "maturity": bu["maturity_years"].to_numpy(dtype=float),
        "volatility": bu["annual_volatility_pct"].to_numpy(dtype=float) / 100.0,
        "aaa_mask": (bu["rating_bucket"] == "AAA").to_numpy(dtype=bool),
        "b_mask": bu["rating_bucket"].isin(["BBB", "BB"]).to_numpy(dtype=bool),
    }


def build_mip_model(bond_universe: pd.DataFrame, constraint_dict: dict) -> ConcreteModel:
    # config for model is the constraint dictionary passed through 
    config = constraint_dict
    bond_pool = bond_universe["bond_id"].tolist()

    min_inc = bond_universe.set_index("bond_id")["minimum_increment"].to_dict()
    exp_ret = (bond_universe.set_index("bond_id")["expected_annual_return_pct"] / 100.0).to_dict()
    liq_score = bond_universe.set_index("bond_id")["liquidity_score"].to_dict()
    maturity = bond_universe.set_index("bond_id")["maturity_years"].to_dict()
    volatility = (bond_universe.set_index("bond_id")["annual_volatility_pct"] / 100.0).to_dict()

    aaa_bucket = bond_universe.loc[bond_universe["rating_bucket"] == "AAA", "bond_id"].tolist()
    b_bucket = bond_universe.loc[
        bond_universe["rating_bucket"].isin(["BBB", "BB"]), "bond_id"
    ].tolist()

    # instantiate model and available bond pool to select from 
    model = ConcreteModel()
    model.BondPool = Set(initialize=bond_pool)
    model.AAAPool = Set(initialize=aaa_bucket)
    model.BRatingPool = Set(initialize=b_bucket)

    model.min_inc = Param(model.BondPool, initialize=min_inc)
    model.exp_ret = Param(model.BondPool, initialize=exp_ret)
    model.liq_score = Param(model.BondPool, initialize=liq_score)
    model.maturity = Param(model.BondPool, initialize=maturity)
    model.volatility = Param(model.BondPool, initialize=volatility)

    model.x = Var(model.BondPool, domain=NonNegativeIntegers)

    total_expected_return = sum(
        model.x[i] * model.min_inc[i] * model.exp_ret[i] for i in model.BondPool
    )
    model.obj = Objective(expr=total_expected_return, sense=maximize)

    total_face_value = sum(model.x[i] * model.min_inc[i] for i in model.BondPool)
    weighted_liquidity = sum(
        model.x[i] * model.liq_score[i] * model.min_inc[i] for i in model.BondPool
    )
    weighted_maturity = sum(
        model.x[i] * model.maturity[i] * model.min_inc[i] for i in model.BondPool
    )
    weighted_return = sum(
        model.x[i] * model.exp_ret[i] * model.min_inc[i] for i in model.BondPool
    )
    weighted_volatility = sum(
        model.x[i] * model.volatility[i] * model.min_inc[i] for i in model.BondPool
    )
    total_aaa_face_value = sum(model.x[i] * model.min_inc[i] for i in model.AAAPool)
    total_b_face_value = sum(model.x[i] * model.min_inc[i] for i in model.BRatingPool)

    # defining model constraints 
    model.min_fv = Constraint(expr=total_face_value >= config["fv_min"])
    model.max_fv = Constraint(expr=total_face_value <= config["fv_max"])
    model.min_liq = Constraint(expr=weighted_liquidity >= config["liq_min"] * total_face_value)
    model.max_maturity = Constraint(expr=weighted_maturity <= config["mat_max"] * total_face_value)
    model.min_return = Constraint(expr=weighted_return >= config["ret_min"] * total_face_value)
    model.aaa_min = Constraint(expr=total_aaa_face_value >= config["aaa_min"] * total_face_value)
    model.b_max = Constraint(expr=total_b_face_value <= config["bbb_bb_max"] * total_face_value)
    model.max_volatility = Constraint(
        expr=weighted_volatility <= config["vol_max"] * total_face_value
    )

    return model


def mip_solver(model: ConcreteModel, solver_name: str = "highs"):
    solver = SolverFactory(solver_name)
    if not solver.available():
        raise RuntimeError(
            f"Solver '{solver_name}' is not available. "
            "For HiGHS, ensure 'highspy' is installed: pip install highspy"
        )
    results = solver.solve(model, tee=False, load_solutions=False)
    if results.solver.termination_condition == TerminationCondition.optimal:
        model.solutions.load_from(results)
    return results


def get_results(model: ConcreteModel, bond_universe: pd.DataFrame) -> pd.DataFrame:
    portfolio_rows: list[dict] = []
    for bond_id in model.BondPool:
        increments_allocated = int(round(value(model.x[bond_id]) or 0))
        if increments_allocated < 1:
            continue
        min_increment = float(value(model.min_inc[bond_id]))
        portfolio_rows.append({
            "bond_id": bond_id,
            "increments_allocated": increments_allocated,
            "fv_allocated": increments_allocated * min_increment,
        })

    if not portfolio_rows:
        return pd.DataFrame(
            columns=["bond_id", "increments_allocated", "fv_allocated", "portfolio_weight",
                     "bond_type", "rating_bucket", "market_price",
                     "expected_annual_return_pct", "liquidity_score",
                     "maturity_years", "annual_volatility_pct"]
        )

    portfolio_df = pd.DataFrame(portfolio_rows)
    portfolio_df = portfolio_df.merge(
        bond_universe[[
            "bond_id", "bond_type", "rating_bucket", "market_price",
            "expected_annual_return_pct", "liquidity_score",
            "maturity_years", "annual_volatility_pct",
        ]],
        on="bond_id", how="left",
    )
    total_face_value = portfolio_df["fv_allocated"].sum()
    portfolio_df["portfolio_weight"] = portfolio_df["fv_allocated"] / total_face_value
    return portfolio_df[[
        "bond_id", "increments_allocated", "fv_allocated", "portfolio_weight",
        "bond_type", "rating_bucket", "market_price",
        "expected_annual_return_pct", "liquidity_score",
        "maturity_years", "annual_volatility_pct",
    ]]

"""
# portfolio risk evaluation, which has been vectorized for optimal performance. 
# uses pre-cast numpy covariance array and
# integer index map to avoid pandas .loc function call overhead for each scenario. 
 """
def eval_portfolio_risk_vectorized(
    selected_bonds: pd.DataFrame,
    cov_np: np.ndarray,
    id_to_idx: dict[str, int],
) -> dict[str, object]:
    # make sure bond selection is not empty 
    if selected_bonds.empty:
        return {"variance": 0.0, "volatility": 0.0, "correlation_matrix": pd.DataFrame()}

    bond_ids = selected_bonds["bond_id"].tolist()
    idx = [id_to_idx[b] for b in bond_ids]
    sigma_sub = cov_np[np.ix_(idx, idx)]
    weights = selected_bonds["portfolio_weight"].to_numpy(dtype=float)

    variance = float(weights @ sigma_sub @ weights)
    volatility = float(np.sqrt(max(variance, 0.0)))
    std_vector = np.sqrt(np.clip(np.diag(sigma_sub), 0.0, None))
    denom = np.outer(std_vector, std_vector)
    corr_values = np.divide(
        sigma_sub, denom,
        out=np.zeros_like(sigma_sub, dtype=float),
        where=denom > 0,
    )
    correlation_matrix = pd.DataFrame(corr_values, index=bond_ids, columns=bond_ids)
    return {"variance": variance, "volatility": volatility, "correlation_matrix": correlation_matrix}


def summarize_portfolio(
    portfolio_df: pd.DataFrame,
    risk_metrics: dict[str, object] | None = None,
) -> dict[str, float]:
    if portfolio_df.empty:
        return {
            "selected_bond_count": 0, "total_face_value": 0.0,
            "weighted_expected_return_pct": 0.0, "weighted_liquidity_score": 0.0,
            "weighted_maturity_years": 0.0, "weighted_annual_volatility_pct": 0.0,
            "portfolio_variance": 0.0, "portfolio_volatility": 0.0,
        }
    weights = portfolio_df["portfolio_weight"].to_numpy(dtype=float)
    summary = {
        "selected_bond_count": int(len(portfolio_df)),
        "total_face_value": float(portfolio_df["fv_allocated"].sum()),
        "weighted_expected_return_pct": float(np.dot(weights, portfolio_df["expected_annual_return_pct"])),
        "weighted_liquidity_score": float(np.dot(weights, portfolio_df["liquidity_score"])),
        "weighted_maturity_years": float(np.dot(weights, portfolio_df["maturity_years"])),
        "weighted_annual_volatility_pct": float(np.dot(weights, portfolio_df["annual_volatility_pct"])),
        "portfolio_variance": 0.0,
        "portfolio_volatility": 0.0,
    }
    if risk_metrics:
        summary["portfolio_variance"] = float(risk_metrics["variance"])
        summary["portfolio_volatility"] = float(risk_metrics["volatility"])
    return summary

"""
# _solve_single_scenario: worker function to solve a single bond scenario 
"""
def _solve_single_scenario(args: tuple) -> tuple[int, dict[str, object]]:
    scenario_id, config, bond_universe_dict, cov_np, id_to_idx, solver_name = args

    bond_universe = pd.DataFrame(bond_universe_dict)

    try:
        model = build_mip_model(bond_universe, config)
        start_time = time.time()
        results = mip_solver(model, solver_name=solver_name)
        solve_time_seconds = time.time() - start_time

        optimal = (
            results.solver.status == SolverStatus.ok
            and results.solver.termination_condition == TerminationCondition.optimal
        )
        if not optimal:
            status = str(results.solver.termination_condition)
            return scenario_id, {
                "scenario_id": scenario_id,
                "scenario_name": config["name"],
                "status": status,
                "portfolio_df": pd.DataFrame(),
                "summary_metrics": {},
                "solve_time_seconds": solve_time_seconds,
            }

        portfolio_df = get_results(model, bond_universe)
        risk_metrics = (
            eval_portfolio_risk_vectorized(portfolio_df, cov_np, id_to_idx)
            if cov_np is not None else None
        )
        summary_metrics = summarize_portfolio(portfolio_df, risk_metrics)
        objective_value = float(value(model.obj))

        return scenario_id, {
            "scenario_id": scenario_id,
            "scenario_name": config["name"],
            "status": "Optimal",
            "objective_value": objective_value,
            "solve_time_seconds": solve_time_seconds,
            "portfolio_df": portfolio_df,
            "summary_metrics": summary_metrics,
            "risk_metrics": risk_metrics,
            "model": None,  # Pyomo models can't cross process boundaries
        }
    except Exception as exc:
        return scenario_id, {
            "scenario_id": scenario_id,
            "scenario_name": config["name"],
            "status": f"Error: {exc}",
            "portfolio_df": pd.DataFrame(),
            "summary_metrics": {},
            "solve_time_seconds": None,
        }

"""
# run_all_scenarios_parallel(): parallelized bond scenario solvers. replaces run_all_scenarios, 
# which solves each bond scenario sequentially. 
"""
def run_all_scenarios_parallel(
    bond_universe: pd.DataFrame,
    cov_matrix: pd.DataFrame | None = None,
    solver_name: str = "highs",
    n_workers: int | None = None,
) -> dict[int, dict[str, object]]:
    # set n workers to minimum # of bond scenarios, if no param passed into function
    n_workers = n_workers or min(len(CONSTRAINTS), os.cpu_count() or 1)

    cov_np: np.ndarray | None = None
    id_to_idx: dict[str, int] = {}
    if cov_matrix is not None:
        cov_np = cov_matrix.to_numpy(dtype=float)
        ids = list(cov_matrix.index.astype(str))
        id_to_idx = {bid: i for i, bid in enumerate(ids)}

    bond_universe_dict = bond_universe.to_dict(orient="list")
    args = [
        (sid, config, bond_universe_dict, cov_np, id_to_idx, solver_name)
        for sid, config in CONSTRAINTS.items()
    ]

    # delegate each worker to solve 1 bond scenario in parallel 
    with Pool(n_workers) as pool:
        paired = pool.map(_solve_single_scenario, args)

    return dict(paired)


def load_default_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    bond_universe = pd.read_csv(DATA_DIR / "synthetic_bond_universe.csv")
    cov_matrix = pd.read_csv(DATA_DIR / "synthetic_covariance_matrix.csv", index_col=0)
    return bond_universe, cov_matrix


if __name__ == "__main__":
    default_bond_universe, default_cov_matrix = load_default_inputs()
    run_all_scenarios_parallel(default_bond_universe, cov_matrix=default_cov_matrix)
