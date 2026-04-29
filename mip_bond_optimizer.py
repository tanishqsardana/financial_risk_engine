from __future__ import annotations

import time
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


CONSTRAINTS = {
    1: dict(
        name="Portfolio 1 — ~$50M target value, medium time horizon",
        fv_min=50_000_000,
        fv_max=50_500_000,
        liq_min=0.85,
        mat_max=20,
        ret_min=0.03,
        aaa_min=0.60,
        bbb_bb_max=0.10,
        vol_max=0.05,
    ),
    2: dict(
        name="Portfolio 2 — ~$20M target value, short time horizon, risk-averse",
        fv_min=20_000_000,
        fv_max=20_500_000,
        liq_min=0.95,
        mat_max=10,
        ret_min=0.03,
        aaa_min=0.80,
        bbb_bb_max=0.05,
        vol_max=0.02,
    ),
    3: dict(
        name="Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk",
        fv_min=100_000_000,
        fv_max=101_500_000,
        liq_min=0.70,
        mat_max=30,
        ret_min=0.03,
        aaa_min=0.80,
        bbb_bb_max=0.05,
        vol_max=0.05,
    ),
}


def build_mip_model(bond_universe: pd.DataFrame, constraint_dict: dict) -> ConcreteModel:
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

    model.min_fv = Constraint(expr=total_face_value >= config["fv_min"])
    model.max_fv = Constraint(expr=total_face_value <= config["fv_max"])
    model.min_liq = Constraint(expr=weighted_liquidity >= config["liq_min"] * total_face_value)
    model.max_maturity = Constraint(
        expr=weighted_maturity <= config["mat_max"] * total_face_value
    )
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
    portfolio_rows: list[dict[str, float | str]] = []
    for bond_id in model.BondPool:
        increments_allocated = int(round(value(model.x[bond_id]) or 0))
        if increments_allocated < 1:
            continue
        min_increment = float(value(model.min_inc[bond_id]))
        portfolio_rows.append(
            {
                "bond_id": bond_id,
                "increments_allocated": increments_allocated,
                "fv_allocated": increments_allocated * min_increment,
            }
        )

    if not portfolio_rows:
        return pd.DataFrame(
            columns=[
                "bond_id",
                "increments_allocated",
                "fv_allocated",
                "portfolio_weight",
                "bond_type",
                "rating_bucket",
                "market_price",
                "expected_annual_return_pct",
                "liquidity_score",
                "maturity_years",
                "annual_volatility_pct",
            ]
        )

    portfolio_df = pd.DataFrame(portfolio_rows)
    portfolio_df = portfolio_df.merge(
        bond_universe[
            [
                "bond_id",
                "bond_type",
                "rating_bucket",
                "market_price",
                "expected_annual_return_pct",
                "liquidity_score",
                "maturity_years",
                "annual_volatility_pct",
            ]
        ],
        on="bond_id",
        how="left",
    )

    total_face_value = portfolio_df["fv_allocated"].sum()
    portfolio_df["portfolio_weight"] = portfolio_df["fv_allocated"] / total_face_value

    return portfolio_df[
        [
            "bond_id",
            "increments_allocated",
            "fv_allocated",
            "portfolio_weight",
            "bond_type",
            "rating_bucket",
            "market_price",
            "expected_annual_return_pct",
            "liquidity_score",
            "maturity_years",
            "annual_volatility_pct",
        ]
    ]


def eval_portfolio_risk(selected_bonds: pd.DataFrame, cov_matrix: pd.DataFrame) -> dict[str, object]:
    if selected_bonds.empty:
        return {
            "variance": 0.0,
            "volatility": 0.0,
            "correlation_matrix": pd.DataFrame(),
        }

    bond_ids = selected_bonds["bond_id"].tolist()
    sigma = cov_matrix.loc[bond_ids, bond_ids]
    weights = selected_bonds["portfolio_weight"].to_numpy(dtype=float)
    sigma_values = sigma.to_numpy(dtype=float)

    variance = float(weights.T @ sigma_values @ weights)
    volatility = float(np.sqrt(max(variance, 0.0)))
    std_vector = np.sqrt(np.clip(np.diag(sigma_values), a_min=0.0, a_max=None))
    denom = np.outer(std_vector, std_vector)
    correlation_values = np.divide(
        sigma_values,
        denom,
        out=np.zeros_like(sigma_values, dtype=float),
        where=denom > 0,
    )
    correlation_matrix = pd.DataFrame(correlation_values, index=bond_ids, columns=bond_ids)

    return {
        "variance": variance,
        "volatility": volatility,
        "correlation_matrix": correlation_matrix,
    }


def summarize_portfolio(portfolio_df: pd.DataFrame, risk_metrics: dict[str, object] | None = None) -> dict[str, float]:
    if portfolio_df.empty:
        return {
            "selected_bond_count": 0,
            "total_face_value": 0.0,
            "weighted_expected_return_pct": 0.0,
            "weighted_liquidity_score": 0.0,
            "weighted_maturity_years": 0.0,
            "weighted_annual_volatility_pct": 0.0,
            "portfolio_variance": 0.0,
            "portfolio_volatility": 0.0,
        }

    weights = portfolio_df["portfolio_weight"]
    summary = {
        "selected_bond_count": int(len(portfolio_df)),
        "total_face_value": float(portfolio_df["fv_allocated"].sum()),
        "weighted_expected_return_pct": float(
            np.dot(weights, portfolio_df["expected_annual_return_pct"])
        ),
        "weighted_liquidity_score": float(np.dot(weights, portfolio_df["liquidity_score"])),
        "weighted_maturity_years": float(np.dot(weights, portfolio_df["maturity_years"])),
        "weighted_annual_volatility_pct": float(
            np.dot(weights, portfolio_df["annual_volatility_pct"])
        ),
        "portfolio_variance": 0.0,
        "portfolio_volatility": 0.0,
    }

    if risk_metrics:
        summary["portfolio_variance"] = float(risk_metrics["variance"])
        summary["portfolio_volatility"] = float(risk_metrics["volatility"])

    return summary


def run_all_scenarios(
    bond_universe: pd.DataFrame,
    cov_matrix: pd.DataFrame | None = None,
    solver_name: str = "highs",
) -> dict[int, dict[str, object]]:
    scenario_results: dict[int, dict[str, object]] = {}

    for scenario_id, config in CONSTRAINTS.items():
        print(f"Running Bond Scenario: {config['name']}")
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
                print(f"Warning: Could not find an optimal solution. Status: {status}\n")
                scenario_results[scenario_id] = {
                    "scenario_id": scenario_id,
                    "scenario_name": config["name"],
                    "status": status,
                    "portfolio_df": pd.DataFrame(),
                    "summary_metrics": {},
                    "model": model,
                    "solve_time_seconds": solve_time_seconds,
                }
                continue

            portfolio_df = get_results(model, bond_universe)
            risk_metrics = eval_portfolio_risk(portfolio_df, cov_matrix) if cov_matrix is not None else None
            summary_metrics = summarize_portfolio(portfolio_df, risk_metrics)
            objective_value = float(value(model.obj))

            print("Status: Optimal Solution Found")
            print(f"Portfolio Expected Return ($): {objective_value:,.5f}")
            print(f"Solve Time: {solve_time_seconds:.5f} seconds")
            print(f"Selected Bonds: {summary_metrics['selected_bond_count']}")
            if risk_metrics is not None:
                print(f"Portfolio Volatility: {summary_metrics['portfolio_volatility']:.6f}")
            print()

            scenario_results[scenario_id] = {
                "scenario_id": scenario_id,
                "scenario_name": config["name"],
                "status": "Optimal",
                "objective_value": objective_value,
                "solve_time_seconds": solve_time_seconds,
                "portfolio_df": portfolio_df,
                "summary_metrics": summary_metrics,
                "risk_metrics": risk_metrics,
                "model": model,
            }
        except Exception as exc:
            print(f"Error processing {config['name']}: {exc}\n")
            scenario_results[scenario_id] = {
                "scenario_id": scenario_id,
                "scenario_name": config["name"],
                "status": f"Error: {exc}",
                "portfolio_df": pd.DataFrame(),
                "summary_metrics": {},
                "solve_time_seconds": None,
            }

    return scenario_results


def load_default_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    bond_universe = pd.read_csv(DATA_DIR / "synthetic_bond_universe.csv")
    cov_matrix = pd.read_csv(DATA_DIR / "synthetic_covariance_matrix.csv", index_col=0)
    return bond_universe, cov_matrix


if __name__ == "__main__":
    default_bond_universe, default_cov_matrix = load_default_inputs()
    run_all_scenarios(default_bond_universe, cov_matrix=default_cov_matrix)
