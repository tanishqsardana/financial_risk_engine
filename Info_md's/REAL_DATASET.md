# Real Bond Dataset

This dataset is the non-synthetic companion to the larger synthetic bond universe. It is built from real bond benchmark series from FRED plus real bond ETF histories.

## What it contains

- `real_data/real_bond_asset_metadata.csv`
- `real_data/real_bond_assets_daily.csv`
- `real_data/real_bond_daily_returns.csv`
- `real_data/real_bond_monthly_returns.csv`
- `real_data/real_bond_factors_monthly.csv`
- `real_data/real_bond_daily_covariance_matrix.csv`
- `real_data/real_bond_monthly_covariance_matrix.csv`
- `real_data/real_dataset_manifest.csv`

## Asset universe

The asset panel is composed of real bond benchmarks and real bond ETFs rather than synthetic bond rows:

- ICE BofA US Corporate broad and rating buckets
- ICE BofA US High Yield broad and rating buckets
- ICE BofA Emerging Markets Corporate broad, high-grade, and high-yield buckets
- OMRX Municipal Bond Index
- Bond ETFs such as AGG, BND, LQD, VCIT, VCSH, HYG, JNK, MUB, TIP, EMB, BNDX, IEF, TLT, and SHY

## Important limitation

This dataset is fully real at the asset level, but it is not issue-level bond data. If you need actual individual bond records with CUSIPs, coupons, and transaction-level prices, the clean public sources become much harder to automate and usually require workflow-heavy or paid data access.

## Licensing note

The benchmark series are pulled from FRED. The ETF histories are pulled from Yahoo Finance's public chart endpoint using adjusted close prices. Those underlying providers still control their own usage terms.
