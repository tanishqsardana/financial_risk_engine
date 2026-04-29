➜  financial_risk_engine git:(apds-optimized-scripts) ✗ /opt/anaconda3/bin/python3.13 run_full_pipeline_optimized.py
Running Bond Scenario: Portfolio 1 — ~$50M target value, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 2,428,903.75000
Solve Time: 0.22682 seconds
Selected Bonds: 4
Portfolio Volatility: 0.084422

Running Bond Scenario: Portfolio 2 — ~$20M target value, short time horizon, risk-averse
Warning: Could not find an optimal solution. Status: infeasible

Running Bond Scenario: Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk
Status: Optimal Solution Found
Portfolio Expected Return ($): 4,632,616.70000
Solve Time: 0.13937 seconds
Selected Bonds: 4
Portfolio Volatility: 0.091100

Running Bond Scenario: Portfolio 4 — ~$20M target value, short time horizon, risk-averse
Status: Optimal Solution Found
Portfolio Expected Return ($): 759,476.47000
Solve Time: 0.45701 seconds
Selected Bonds: 8
Portfolio Volatility: 0.033740

Running Bond Scenario: Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile
Status: Optimal Solution Found
Portfolio Expected Return ($): 19,469,580.65000
Solve Time: 0.22229 seconds
Selected Bonds: 4
Portfolio Volatility: 0.020747

Running Bond Scenario: Portfolio 6 — ~$75M target value, balanced risk, longer time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 3,275,510.54000
Solve Time: 0.21589 seconds
Selected Bonds: 4
Portfolio Volatility: 0.053082

Running Bond Scenario: Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 9,949,618.56000
Solve Time: 0.31471 seconds
Selected Bonds: 8
Portfolio Volatility: 0.059080

Running Bond Scenario: Portfolio 1 — ~$50M target value, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 2,428,903.75000
Solve Time: 0.21868 seconds
Selected Bonds: 4
Portfolio Volatility: 0.084422

Running Bond Scenario: Portfolio 2 — ~$20M target value, short time horizon, risk-averse
Warning: Could not find an optimal solution. Status: infeasible

Running Bond Scenario: Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk
Status: Optimal Solution Found
Portfolio Expected Return ($): 4,632,616.70000
Solve Time: 0.14001 seconds
Selected Bonds: 4
Portfolio Volatility: 0.091100

Running Bond Scenario: Portfolio 4 — ~$20M target value, short time horizon, risk-averse
Status: Optimal Solution Found
Portfolio Expected Return ($): 759,476.47000
Solve Time: 0.45808 seconds
Selected Bonds: 8
Portfolio Volatility: 0.033740

Running Bond Scenario: Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile
Status: Optimal Solution Found
Portfolio Expected Return ($): 19,469,580.65000
Solve Time: 0.22135 seconds
Selected Bonds: 4
Portfolio Volatility: 0.020747

Running Bond Scenario: Portfolio 6 — ~$75M target value, balanced risk, longer time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 3,275,510.54000
Solve Time: 0.21615 seconds
Selected Bonds: 4
Portfolio Volatility: 0.053082

Running Bond Scenario: Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 9,949,618.56000
Solve Time: 0.31589 seconds
Selected Bonds: 8
Portfolio Volatility: 0.059080

Running Bond Scenario: Portfolio 1 — ~$50M target value, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 2,428,903.75000
Solve Time: 0.22043 seconds
Selected Bonds: 4
Portfolio Volatility: 0.084422

Running Bond Scenario: Portfolio 2 — ~$20M target value, short time horizon, risk-averse
Warning: Could not find an optimal solution. Status: infeasible

Running Bond Scenario: Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk
Status: Optimal Solution Found
Portfolio Expected Return ($): 4,632,616.70000
Solve Time: 0.13882 seconds
Selected Bonds: 4
Portfolio Volatility: 0.091100

Running Bond Scenario: Portfolio 4 — ~$20M target value, short time horizon, risk-averse
Status: Optimal Solution Found
Portfolio Expected Return ($): 759,476.47000
Solve Time: 0.45958 seconds
Selected Bonds: 8
Portfolio Volatility: 0.033740

Running Bond Scenario: Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile
Status: Optimal Solution Found
Portfolio Expected Return ($): 19,469,580.65000
Solve Time: 0.22238 seconds
Selected Bonds: 4
Portfolio Volatility: 0.020747

Running Bond Scenario: Portfolio 6 — ~$75M target value, balanced risk, longer time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 3,275,510.54000
Solve Time: 0.21617 seconds
Selected Bonds: 4
Portfolio Volatility: 0.053082

Running Bond Scenario: Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 9,949,618.56000
Solve Time: 0.31615 seconds
Selected Bonds: 8
Portfolio Volatility: 0.059080


                            Technique  Baseline (s)  Optimized (s)  Speedup
             T1  Vectorized risk eval        0.0002         0.0001     3.20
           T2  Parallel MIP scenarios        1.6389         1.1568     1.42
            T3  Cython MC (n=100,000)        0.0236         0.0027     8.74
   T4  Multiprocessing MC (n=100,000)        0.0076         0.6289     0.01
T5  Parallel stress tests (n=100,000)        0.0354         0.5462     0.06
       T6  Parallel solver comparison        2.0676         1.2952     1.60
   T7  Parallel cov benchmark (avg/5)        0.0542         0.8660     0.06
                       TOTAL PIPELINE        3.1859         4.1805     0.76pi