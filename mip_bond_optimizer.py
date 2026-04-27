import pandas as pd
import numpy as np
import time
import os 
import shutil
from pyomo.environ import *

import opt_utils

""""
# This this the mixed integer linear program (MIP) for bond portfolio construction. 
#
# Problem formulation: 
# - objective function: maximize expected return of bond portfolio 
# - constraints: outlined for each bond scenario in global constant CONSTRAINTS. 
#            all constraints are for the selected aggregate bond portfolio - they do 
#            not explicitly apply for the bonds eligible for selection. This is the 
# - solver: Pyomo HiGHS solver 
"""


""" Defining Bond Scenario Aggregate Constraints """
CONSTRAINTS = {
    1: dict(
        name="Portfolio 1 — ~$50M target value, medium time horizon",
        fv_min=50000000,   
        fv_max=50500000,
        liq_min=0.85,        
        mat_max=20,
        ret_min=0.03,
        aaa_min=0.60,        
        bbb_bb_max=0.10,
        vol_max=0.05,
    ),
    2: dict(
        name="Portfolio 2 — ~$20M target value, short time horizon, risk-averse",
        fv_min=20000000,   
        fv_max=20500000,
        liq_min=0.95,        
        mat_max=10,
        ret_min=0.03,
        aaa_min=0.80,        
        bbb_bb_max=0.05,
        vol_max=0.02,
    ),
    3: dict(
        name="Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk",
        fv_min=100000000,  
        fv_max=101500000,
        liq_min=0.70,        
        mat_max=30,
        ret_min=0.03,
        aaa_min=0.80,        
        bbb_bb_max=0.05,
        vol_max=0.05,
    ),
}

""" 
# Function: Build Model
# building model using pyomo library for bond mixed-integer linear programming 
"""
def build_mip_model(bond_universe: pd.DataFrame, constraint_dict: dict):
    config = constraint_dict
    bond_pool = bond_universe['bond_id'].to_list()

    # process parameters and load into dictionary for constraints 
    min_inc = bond_universe.set_index('bond_id')["minimum_increment"].to_dict()
    exp_ret = (bond_universe.set_index("bond_id")["expected_annual_return_pct"] / 100).to_dict()
    liq_score = bond_universe.set_index("bond_id")["liquidity_score"].to_dict()
    mat = bond_universe.set_index("bond_id")["maturity_years"].to_dict()
    vol = (bond_universe.set_index("bond_id")["annual_volatility_pct"] / 100).to_dict()

    # bucketing by bond rating 
    aaa_bucket = bond_universe.loc[bond_universe['rating_bucket']=='AAA', 'bond_id'].to_list()
    b_bucket = bond_universe.loc[bond_universe['rating_bucket'].isin(['BBB','BB']), 'bond_id'].to_list()


    # instantiate and build out model 
    opt_model = ConcreteModel()
    opt_model.BondPool = Set(initialize = bond_pool)
    opt_model.AAAPool = Set(initialize = aaa_bucket)
    opt_model.BRatingPool = Set(initialize = b_bucket)

    # building out constraint params 
    opt_model.min_inc = Param(opt_model.BondPool, initialize = min_inc)
    opt_model.exp_ret = Param(opt_model.BondPool, initialize = exp_ret)
    opt_model.liq_score = Param(opt_model.BondPool, initialize = liq_score)
    opt_model.mat = Param(opt_model.BondPool, initialize = mat)
    opt_model.vol = Param(opt_model.BondPool, initialize = vol)
    
    """
    # decision variables 
    # variables: x[i] := number of minimum increments of bond index i to include in bond portfolio 
    #            x[i] > 0 if yes, included (integers only)
    #            x[i] = 0 if no, excluded from portfolio
    """
    opt_model.x = Var(opt_model.BondPool, domain = NonNegativeIntegers)

    """
    # Objective Function: maximize expected return of portfolio
    # mininc_i * x_i * exp_return_i : the number of minimum increments*min increment amount*decision to include bond i*expected return of bond i 
    """
    obj_func = sum(opt_model.x[i]*opt_model.min_inc[i]*opt_model.exp_ret[i] for i in opt_model.BondPool)
    opt_model.obj = Objective(expr=obj_func, sense=maximize)

    """
    Constraints:
    formulating constraints as laid out in constraint dictionary 
    """
    # portfolio face value - used for linearizing weighted average constraints 
    fv = sum(opt_model.x[i] * opt_model.min_inc[i] for i in opt_model.BondPool)

    # constraint 1: target value range of bond portfolio 
    val_range = sum(opt_model.x[i]*opt_model.min_inc[i] for i in opt_model.BondPool)
    opt_model.min_fv = Constraint(expr = val_range >= config['fv_min'])
    opt_model.max_fv = Constraint(expr = val_range <= config['fv_max'])
    
    # constraint 2: time horizon maximum: weighted average 
    wavg_mat = sum(opt_model.x[i]*opt_model.mat[i]*opt_model.min_inc[i] for i in opt_model.BondPool)
   
    # constraint 3: budget - redundant with constraint #1 
   
    # constraint 4: liquidity score acceptable range 
    wavg_liq = sum(opt_model.x[i]*opt_model.liq_score[i]*opt_model.min_inc[i] for i in opt_model.BondPool)
    opt_model.min_liq = Constraint(expr = wavg_liq >= config['liq_min']*fv)
   
    # constraint 5: expected return minimum (greater than inflation benchmark)
    wavg_exp_ret = sum(opt_model.x[i]*opt_model.exp_ret[i]*opt_model.min_inc[i] for i in opt_model.BondPool)
    opt_model.inflation_const = Constraint(expr = wavg_exp_ret >= config['ret_min']*fv)
    
    # constraint 6: minimum AAA percentage 
    wavg_aaa = sum(opt_model.x[i]*opt_model.min_inc[i] for i in opt_model.AAAPool)
    opt_model.aaa_min = Constraint(expr = wavg_aaa >= config['aaa_min']*fv)
    
    # constraint 7: maximum BBB+BB percentage 
    wavg_b = sum(opt_model.x[i]*opt_model.min_inc[i] for i in opt_model.BRatingPool)
    opt_model.b_max = Constraint(expr = wavg_b <= config['bbb_bb_max']*fv)

    return opt_model

"""
Function: mip_solver
"""
def mip_solver(model: object, solver_name:str='appsi_highs'): 
    solver = SolverFactory(solver_name)
    if not solver.available():
        raise RuntimeError(
            f"Solver '{solver_name}' is not available. "
            "For HiGHS, ensure 'highspy' is installed: pip install highspy"
        )
    results = solver.solve(model, tee=False)
    return results


"""
Function: run all scenarios in the global CONSTRAINTS dictionary 
"""
def run_all_scenarios(bond_universe: pd.DataFrame, solver_name: str = 'appsi_highs'):
    scenario_results = {}

    for scenario_id, config in CONSTRAINTS.items():
        print(f"Running Bond Scenario: {config['name']}")
        
        try:
            # 1. Build the model for this specific constraint set
            model = build_mip_model(bond_universe, config)
            
            # 2. Solve the model
            start_time = time.time()
            results = mip_solver(model, solver_name)
            end_time = time.time()

            # 3. Check for feasibility and store results
            if (results.solver.status == SolverStatus.ok) and (results.solver.termination_condition == TerminationCondition.optimal):
                obj_val = value(model.obj)
                print(f"Status: Optimal Solution Found")
                print(f"Portfolio Expected Return ($): {obj_val:,.2f}")
                print(f"Solve Time: {end_time - start_time:.2f} seconds\n")
                print(obj_val)

                scenario_results[scenario_id] = {
                    "model": model,
                    "objective": obj_val,
                    "status": "Optimal"
                }
            else:
                print(f"Warning: Could not find an optimal solution. Status: {results.solver.termination_condition}\n")
                scenario_results[scenario_id] = {"status": str(results.solver.termination_condition)}

        except Exception as e:
            print(f"Error processing {config['name']}: {e}\n")

    return scenario_results


"""
# Get results from model 
"""


"""
# Run script 
"""
if __name__ == "main":
    run_all_scenarios()