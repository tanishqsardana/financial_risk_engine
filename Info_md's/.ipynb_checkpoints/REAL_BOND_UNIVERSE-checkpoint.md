# Real Bond Universe

This file describes the assets used in the real bond universe built in [real_bond_asset_metadata.csv](/Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/real_data/real_bond_asset_metadata.csv).

The universe contains `28` real assets:

- `14` bond benchmark/index series from FRED
- `14` bond ETFs with adjusted-close histories from Yahoo Finance

## Indexes

| Asset ID | Series ID | Asset Name | Segment | Quality Bucket | Source |
| --- | --- | --- | --- | --- | --- |
| `corp_ig_broad` | `BAMLCC0A0CMTRIV` | ICE BofA US Corporate Index | corporate | investment_grade | FRED |
| `corp_aaa` | `BAMLCC0A1AAATRIV` | ICE BofA AAA US Corporate Index | corporate | AAA | FRED |
| `corp_aa` | `BAMLCC0A2AATRIV` | ICE BofA AA US Corporate Index | corporate | AA | FRED |
| `corp_a` | `BAMLCC0A3ATRIV` | ICE BofA Single-A US Corporate Index | corporate | A | FRED |
| `corp_bbb` | `BAMLCC0A4BBBTRIV` | ICE BofA BBB US Corporate Index | corporate | BBB | FRED |
| `corp_1_3y` | `BAMLCC1A013YTRIV` | ICE BofA 1-3 Year US Corporate Index | corporate | investment_grade_short_duration | FRED |
| `hy_broad` | `BAMLHYH0A0HYM2TRIV` | ICE BofA US High Yield Index | high_yield | broad_high_yield | FRED |
| `hy_bb` | `BAMLHYH0A1BBTRIV` | ICE BofA BB US High Yield Index | high_yield | BB | FRED |
| `hy_b` | `BAMLHYH0A2BTRIV` | ICE BofA Single-B US High Yield Index | high_yield | B | FRED |
| `hy_ccc` | `BAMLHYH0A3CMTRIV` | ICE BofA CCC & Lower US High Yield Index | high_yield | CCC_and_lower | FRED |
| `em_broad` | `BAMLEMCBPITRIV` | ICE BofA Emerging Markets Corporate Plus Index | emerging_markets | broad_em | FRED |
| `em_high_grade` | `BAMLEMIBHGCRPITRIV` | ICE BofA High Grade Emerging Markets Corporate Plus Index | emerging_markets | high_grade | FRED |
| `em_high_yield` | `BAMLEMHBHYCRPITRIV` | ICE BofA High Yield Emerging Markets Corporate Plus Index | emerging_markets | high_yield | FRED |
| `municipal_broad` | `NASDAQOMRXMUNI` | OMRX Municipal Bond Index | municipal | broad_municipal | FRED |

## ETFs

| Asset ID | Ticker | Asset Name | Segment | Quality Bucket | Source |
| --- | --- | --- | --- | --- | --- |
| `agg_etf` | `AGG` | iShares Core U.S. Aggregate Bond ETF | aggregate | broad_investment_grade | Yahoo Finance |
| `bnd_etf` | `BND` | Vanguard Total Bond Market ETF | aggregate | broad_investment_grade | Yahoo Finance |
| `lqd_etf` | `LQD` | iShares iBoxx $ Investment Grade Corporate Bond ETF | corporate | investment_grade | Yahoo Finance |
| `vcit_etf` | `VCIT` | Vanguard Intermediate-Term Corporate Bond ETF | corporate | investment_grade_intermediate | Yahoo Finance |
| `vcsh_etf` | `VCSH` | Vanguard Short-Term Corporate Bond ETF | corporate | investment_grade_short_duration | Yahoo Finance |
| `hyg_etf` | `HYG` | iShares iBoxx $ High Yield Corporate Bond ETF | high_yield | broad_high_yield | Yahoo Finance |
| `jnk_etf` | `JNK` | SPDR Bloomberg High Yield Bond ETF | high_yield | broad_high_yield | Yahoo Finance |
| `mub_etf` | `MUB` | iShares National Muni Bond ETF | municipal | broad_municipal | Yahoo Finance |
| `tip_etf` | `TIP` | iShares TIPS Bond ETF | inflation_linked | treasury_tips | Yahoo Finance |
| `emb_etf` | `EMB` | iShares J.P. Morgan USD Emerging Markets Bond ETF | emerging_markets | sovereign_usd | Yahoo Finance |
| `bndx_etf` | `BNDX` | Vanguard Total International Bond ETF | international | broad_international_hedged | Yahoo Finance |
| `ief_etf` | `IEF` | iShares 7-10 Year Treasury Bond ETF | treasury | intermediate_treasury | Yahoo Finance |
| `tlt_etf` | `TLT` | iShares 20+ Year Treasury Bond ETF | treasury | long_treasury | Yahoo Finance |
| `shy_etf` | `SHY` | iShares 1-3 Year Treasury Bond ETF | treasury | short_treasury | Yahoo Finance |

## Why These Assets Were Used

- They are all real bond-market exposures rather than synthetic bonds.
- Together they cover the main fixed-income sleeves used in portfolio construction: Treasury, aggregate bond, investment-grade corporate, high yield, municipal, inflation-linked, emerging-market, and international bond exposure.
- They have overlapping history across the `2016-01` to `2025-12` window used in the real dataset build.
- They are practical for covariance estimation, portfolio optimization, and Monte Carlo experiments because they provide continuous return histories.

## Related Files

- [build_real_bond_dataset.py](/Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/build_real_bond_dataset.py)
- [real_bond_asset_metadata.csv](/Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/real_data/real_bond_asset_metadata.csv)
- [real_bond_monthly_returns.csv](/Users/tanishqsardana/Documents/HW/bond_portfolio_dataset/real_data/real_bond_monthly_returns.csv)
