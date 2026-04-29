Running Bond Scenario: Portfolio 1 — ~$50M target value, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 2,428,903.75000
Solve Time: 0.22885 seconds
Selected Bonds: 4
Portfolio Volatility: 0.084422

Running Bond Scenario: Portfolio 2 — ~$20M target value, short time horizon, risk-averse
Warning: Could not find an optimal solution. Status: infeasible

Running Bond Scenario: Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk
Status: Optimal Solution Found
Portfolio Expected Return ($): 4,632,616.70000
Solve Time: 0.13904 seconds
Selected Bonds: 4
Portfolio Volatility: 0.091100

Running Bond Scenario: Portfolio 4 — ~$20M target value, short time horizon, risk-averse
Status: Optimal Solution Found
Portfolio Expected Return ($): 759,476.47000
Solve Time: 0.46161 seconds
Selected Bonds: 8
Portfolio Volatility: 0.033740

Running Bond Scenario: Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile
Status: Optimal Solution Found
Portfolio Expected Return ($): 19,469,580.65000
Solve Time: 0.22218 seconds
Selected Bonds: 4
Portfolio Volatility: 0.020747

Running Bond Scenario: Portfolio 6 — ~$75M target value, balanced risk, longer time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 3,275,510.54000
Solve Time: 0.21884 seconds
Selected Bonds: 4
Portfolio Volatility: 0.053082

Running Bond Scenario: Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 9,949,618.56000
Solve Time: 0.31647 seconds
Selected Bonds: 8
Portfolio Volatility: 0.059080

Running Bond Scenario: Portfolio 1 — ~$50M target value, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 2,428,903.75000
Solve Time: 0.22180 seconds
Selected Bonds: 4
Portfolio Volatility: 0.084422

Running Bond Scenario: Portfolio 2 — ~$20M target value, short time horizon, risk-averse
Warning: Could not find an optimal solution. Status: infeasible

Running Bond Scenario: Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk
Status: Optimal Solution Found
Portfolio Expected Return ($): 4,632,616.70000
Solve Time: 0.13875 seconds
Selected Bonds: 4
Portfolio Volatility: 0.091100

Running Bond Scenario: Portfolio 4 — ~$20M target value, short time horizon, risk-averse
Status: Optimal Solution Found
Portfolio Expected Return ($): 759,476.47000
Solve Time: 0.48446 seconds
Selected Bonds: 8
Portfolio Volatility: 0.033740

Running Bond Scenario: Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile
Status: Optimal Solution Found
Portfolio Expected Return ($): 19,469,580.65000
Solve Time: 0.23128 seconds
Selected Bonds: 4
Portfolio Volatility: 0.020747

Running Bond Scenario: Portfolio 6 — ~$75M target value, balanced risk, longer time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 3,275,510.54000
Solve Time: 0.21645 seconds
Selected Bonds: 4
Portfolio Volatility: 0.053082

Running Bond Scenario: Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 9,949,618.56000
Solve Time: 0.31702 seconds
Selected Bonds: 8
Portfolio Volatility: 0.059080

Running Bond Scenario: Portfolio 1 — ~$50M target value, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 2,428,903.75000
Solve Time: 0.22248 seconds
Selected Bonds: 4
Portfolio Volatility: 0.084422

Running Bond Scenario: Portfolio 2 — ~$20M target value, short time horizon, risk-averse
Warning: Could not find an optimal solution. Status: infeasible

Running Bond Scenario: Portfolio 3 — ~$100M target value, long time horizon, moderate/high risk
Status: Optimal Solution Found
Portfolio Expected Return ($): 4,632,616.70000
Solve Time: 0.14000 seconds
Selected Bonds: 4
Portfolio Volatility: 0.091100

Running Bond Scenario: Portfolio 4 — ~$20M target value, short time horizon, risk-averse
Status: Optimal Solution Found
Portfolio Expected Return ($): 759,476.47000
Solve Time: 0.46117 seconds
Selected Bonds: 8
Portfolio Volatility: 0.033740

Running Bond Scenario: Portfolio 5 — ~$500M target value (very high face value) medium time horizon, less volatile
Status: Optimal Solution Found
Portfolio Expected Return ($): 19,469,580.65000
Solve Time: 0.22215 seconds
Selected Bonds: 4
Portfolio Volatility: 0.020747

Running Bond Scenario: Portfolio 6 — ~$75M target value, balanced risk, longer time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 3,275,510.54000
Solve Time: 0.21870 seconds
Selected Bonds: 4
Portfolio Volatility: 0.053082

Running Bond Scenario: Portfolio 7 — ~$200M target value, high-value diversified, medium time horizon
Status: Optimal Solution Found
Portfolio Expected Return ($): 9,949,618.56000
Solve Time: 0.31597 seconds
Selected Bonds: 8
Portfolio Volatility: 0.059080


                     Technique  Baseline (s)  Optimized (s)  Speedup
      T1  Vectorized risk eval        0.0002         0.0001     3.22
    T2  Parallel MIP scenarios        1.6798         1.1545     1.45
     T3  Cython MC (n=100,000)        0.0036         0.0026     1.37
T6  Parallel solver comparison        2.1057         1.3051     1.61
                TOTAL PIPELINE        3.2691         0.3291     9.93