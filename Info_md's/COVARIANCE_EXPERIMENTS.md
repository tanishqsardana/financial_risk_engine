# Covariance Experiments

Run the experiment suite with:

```bash
python3 /Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/run_covariance_experiments.py
```

The script reads:

- `real_data/real_bond_monthly_returns.csv`
- `real_data/real_bond_factors_monthly.csv`

It writes:

- `covariance_experiments/covariance_benchmark_results.csv`
- `covariance_experiments/covariance_experiment_sizes.csv`
- `covariance_experiments/covariance_experiment_summary.md`

The benchmark compares:

- naive sample covariance
- factor-model covariance
- `float64` vs `float32`

For scaling tests larger than the 28 observed real assets, the script expands the real panel using return-series clones with small perturbations. That means the timing experiment is rooted in the real dataset, but the large-N panels are derived rather than directly observed.
