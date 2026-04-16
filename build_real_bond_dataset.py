from __future__ import annotations

import csv
import io
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np


START_DATE = date.fromisoformat("2016-01-01")
END_DATE = date.fromisoformat("2025-12-31")
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "real_data"
YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0"}

INDEX_ASSETS = [
    {
        "asset_id": "corp_ig_broad",
        "ticker": "BAMLCC0A0CMTRIV",
        "asset_name": "ICE BofA US Corporate Index",
        "segment": "corporate",
        "quality_bucket": "investment_grade",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "corp_aaa",
        "ticker": "BAMLCC0A1AAATRIV",
        "asset_name": "ICE BofA AAA US Corporate Index",
        "segment": "corporate",
        "quality_bucket": "AAA",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "corp_aa",
        "ticker": "BAMLCC0A2AATRIV",
        "asset_name": "ICE BofA AA US Corporate Index",
        "segment": "corporate",
        "quality_bucket": "AA",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "corp_a",
        "ticker": "BAMLCC0A3ATRIV",
        "asset_name": "ICE BofA Single-A US Corporate Index",
        "segment": "corporate",
        "quality_bucket": "A",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "corp_bbb",
        "ticker": "BAMLCC0A4BBBTRIV",
        "asset_name": "ICE BofA BBB US Corporate Index",
        "segment": "corporate",
        "quality_bucket": "BBB",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "corp_1_3y",
        "ticker": "BAMLCC1A013YTRIV",
        "asset_name": "ICE BofA 1-3 Year US Corporate Index",
        "segment": "corporate",
        "quality_bucket": "investment_grade_short_duration",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "hy_broad",
        "ticker": "BAMLHYH0A0HYM2TRIV",
        "asset_name": "ICE BofA US High Yield Index",
        "segment": "high_yield",
        "quality_bucket": "broad_high_yield",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "hy_bb",
        "ticker": "BAMLHYH0A1BBTRIV",
        "asset_name": "ICE BofA BB US High Yield Index",
        "segment": "high_yield",
        "quality_bucket": "BB",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "hy_b",
        "ticker": "BAMLHYH0A2BTRIV",
        "asset_name": "ICE BofA Single-B US High Yield Index",
        "segment": "high_yield",
        "quality_bucket": "B",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "hy_ccc",
        "ticker": "BAMLHYH0A3CMTRIV",
        "asset_name": "ICE BofA CCC & Lower US High Yield Index",
        "segment": "high_yield",
        "quality_bucket": "CCC_and_lower",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "em_broad",
        "ticker": "BAMLEMCBPITRIV",
        "asset_name": "ICE BofA Emerging Markets Corporate Plus Index",
        "segment": "emerging_markets",
        "quality_bucket": "broad_em",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "em_high_grade",
        "ticker": "BAMLEMIBHGCRPITRIV",
        "asset_name": "ICE BofA High Grade Emerging Markets Corporate Plus Index",
        "segment": "emerging_markets",
        "quality_bucket": "high_grade",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "em_high_yield",
        "ticker": "BAMLEMHBHYCRPITRIV",
        "asset_name": "ICE BofA High Yield Emerging Markets Corporate Plus Index",
        "segment": "emerging_markets",
        "quality_bucket": "high_yield",
        "asset_type": "index",
        "source": "FRED",
    },
    {
        "asset_id": "municipal_broad",
        "ticker": "NASDAQOMRXMUNI",
        "asset_name": "OMRX Municipal Bond Index",
        "segment": "municipal",
        "quality_bucket": "broad_municipal",
        "asset_type": "index",
        "source": "FRED",
    },
]

ETF_ASSETS = [
    {
        "asset_id": "agg_etf",
        "ticker": "AGG",
        "asset_name": "iShares Core U.S. Aggregate Bond ETF",
        "segment": "aggregate",
        "quality_bucket": "broad_investment_grade",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "bnd_etf",
        "ticker": "BND",
        "asset_name": "Vanguard Total Bond Market ETF",
        "segment": "aggregate",
        "quality_bucket": "broad_investment_grade",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "lqd_etf",
        "ticker": "LQD",
        "asset_name": "iShares iBoxx $ Investment Grade Corporate Bond ETF",
        "segment": "corporate",
        "quality_bucket": "investment_grade",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "vcit_etf",
        "ticker": "VCIT",
        "asset_name": "Vanguard Intermediate-Term Corporate Bond ETF",
        "segment": "corporate",
        "quality_bucket": "investment_grade_intermediate",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "vcsh_etf",
        "ticker": "VCSH",
        "asset_name": "Vanguard Short-Term Corporate Bond ETF",
        "segment": "corporate",
        "quality_bucket": "investment_grade_short_duration",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "hyg_etf",
        "ticker": "HYG",
        "asset_name": "iShares iBoxx $ High Yield Corporate Bond ETF",
        "segment": "high_yield",
        "quality_bucket": "broad_high_yield",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "jnk_etf",
        "ticker": "JNK",
        "asset_name": "SPDR Bloomberg High Yield Bond ETF",
        "segment": "high_yield",
        "quality_bucket": "broad_high_yield",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "mub_etf",
        "ticker": "MUB",
        "asset_name": "iShares National Muni Bond ETF",
        "segment": "municipal",
        "quality_bucket": "broad_municipal",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "tip_etf",
        "ticker": "TIP",
        "asset_name": "iShares TIPS Bond ETF",
        "segment": "inflation_linked",
        "quality_bucket": "treasury_tips",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "emb_etf",
        "ticker": "EMB",
        "asset_name": "iShares J.P. Morgan USD Emerging Markets Bond ETF",
        "segment": "emerging_markets",
        "quality_bucket": "sovereign_usd",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "bndx_etf",
        "ticker": "BNDX",
        "asset_name": "Vanguard Total International Bond ETF",
        "segment": "international",
        "quality_bucket": "broad_international_hedged",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "ief_etf",
        "ticker": "IEF",
        "asset_name": "iShares 7-10 Year Treasury Bond ETF",
        "segment": "treasury",
        "quality_bucket": "intermediate_treasury",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "tlt_etf",
        "ticker": "TLT",
        "asset_name": "iShares 20+ Year Treasury Bond ETF",
        "segment": "treasury",
        "quality_bucket": "long_treasury",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
    {
        "asset_id": "shy_etf",
        "ticker": "SHY",
        "asset_name": "iShares 1-3 Year Treasury Bond ETF",
        "segment": "treasury",
        "quality_bucket": "short_treasury",
        "asset_type": "etf",
        "source": "Yahoo Finance",
    },
]

ALL_ASSETS = INDEX_ASSETS + ETF_ASSETS

FACTOR_SERIES = [
    ("aaa_yield_pct", "AAA"),
    ("baa_yield_pct", "BAA"),
    ("treasury_2y_pct", "GS2"),
    ("treasury_5y_pct", "GS5"),
    ("treasury_10y_pct", "GS10"),
    ("treasury_30y_pct", "GS30"),
]


def fetch_url(url: str, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_fred_series(series_id: str) -> list[tuple[date, float]]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    raw = fetch_url(url).decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    rows: list[tuple[date, float]] = []
    for row in reader:
        obs_date = date.fromisoformat(row["observation_date"])
        if obs_date < START_DATE or obs_date > END_DATE:
            continue
        value = row[series_id]
        if value in {"", "."}:
            continue
        rows.append((obs_date, float(value)))
    return rows


def fetch_yahoo_adjusted_close(ticker: str) -> list[tuple[date, float]]:
    period1 = int(datetime(START_DATE.year, START_DATE.month, START_DATE.day, tzinfo=timezone.utc).timestamp())
    period2_date = END_DATE + timedelta(days=1)
    period2 = int(
        datetime(period2_date.year, period2_date.month, period2_date.day, tzinfo=timezone.utc).timestamp()
    )
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?period1={period1}&period2={period2}&interval=1d&includeAdjustedClose=true"
    )
    raw = fetch_url(url, headers=YAHOO_HEADERS).decode("utf-8")
    payload = json.loads(raw)
    result = payload.get("chart", {}).get("result")
    if not result:
        error = payload.get("chart", {}).get("error")
        raise RuntimeError(f"Yahoo Finance returned no data for {ticker}: {error}")

    node = result[0]
    timestamps = node.get("timestamp", [])
    indicators = node.get("indicators", {})
    adjusted = indicators.get("adjclose", [{}])[0].get("adjclose", [])
    closes = indicators.get("quote", [{}])[0].get("close", [])
    values = adjusted if adjusted else closes

    rows: list[tuple[date, float]] = []
    for ts, value in zip(timestamps, values):
        if value is None:
            continue
        obs_date = datetime.fromtimestamp(ts, timezone.utc).date()
        if obs_date < START_DATE or obs_date > END_DATE:
            continue
        rows.append((obs_date, float(value)))
    return rows


def fetch_asset_levels(asset: dict[str, str]) -> list[tuple[date, float]]:
    if asset["source"] == "FRED":
        return fetch_fred_series(asset["ticker"])
    if asset["source"] == "Yahoo Finance":
        rows = fetch_yahoo_adjusted_close(asset["ticker"])
        time.sleep(0.35)
        return rows
    raise ValueError(f"Unsupported source: {asset['source']}")


def build_factor_rows() -> list[dict[str, object]]:
    merged: dict[date, dict[str, float]] = {}
    for column_name, series_id in FACTOR_SERIES:
        for obs_date, value in fetch_fred_series(series_id):
            merged.setdefault(obs_date, {})[column_name] = value

    rows: list[dict[str, object]] = []
    for obs_date in sorted(merged):
        row = merged[obs_date]
        if len(row) != len(FACTOR_SERIES):
            continue
        rows.append(
            {
                "date": obs_date.isoformat(),
                "aaa_yield_pct": round(row["aaa_yield_pct"], 6),
                "baa_yield_pct": round(row["baa_yield_pct"], 6),
                "treasury_2y_pct": round(row["treasury_2y_pct"], 6),
                "treasury_5y_pct": round(row["treasury_5y_pct"], 6),
                "treasury_10y_pct": round(row["treasury_10y_pct"], 6),
                "treasury_30y_pct": round(row["treasury_30y_pct"], 6),
                "corp_baa_aaa_spread_pct": round(row["baa_yield_pct"] - row["aaa_yield_pct"], 6),
                "treasury_slope_10y_2y_pct": round(
                    row["treasury_10y_pct"] - row["treasury_2y_pct"], 6
                ),
            }
        )
    return rows


def compute_period_returns(level_rows: list[tuple[date, float]]) -> list[tuple[date, float, float]]:
    output: list[tuple[date, float, float]] = []
    previous_level: float | None = None
    for obs_date, level in sorted(level_rows):
        if previous_level is None:
            period_return = 0.0
        else:
            period_return = level / previous_level - 1.0
        output.append((obs_date, level, period_return))
        previous_level = level
    return output


def month_end_rows(level_rows: list[tuple[date, float]]) -> list[tuple[str, float]]:
    month_last: dict[str, float] = {}
    for obs_date, level in sorted(level_rows):
        month_last[f"{obs_date.year:04d}-{obs_date.month:02d}"] = level
    return sorted(month_last.items())


def compute_monthly_returns(month_rows: list[tuple[str, float]]) -> list[tuple[str, float]]:
    output: list[tuple[str, float]] = []
    previous_level: float | None = None
    for month_key, level in month_rows:
        if previous_level is None:
            monthly_return = 0.0
        else:
            monthly_return = level / previous_level - 1.0
        output.append((month_key, monthly_return))
        previous_level = level
    return output


def pairwise_covariance(
    series_by_asset: dict[str, dict[object, float]], asset_ids: list[str], annualization: float
) -> np.ndarray:
    matrix = np.zeros((len(asset_ids), len(asset_ids)))
    for i, asset_i in enumerate(asset_ids):
        for j, asset_j in enumerate(asset_ids):
            common_keys = sorted(set(series_by_asset[asset_i]) & set(series_by_asset[asset_j]))
            if len(common_keys) < 2:
                matrix[i, j] = np.nan
                continue
            x = np.array([series_by_asset[asset_i][key] for key in common_keys], dtype=float)
            y = np.array([series_by_asset[asset_j][key] for key in common_keys], dtype=float)
            matrix[i, j] = float(np.cov(x, y, ddof=1)[0, 1] * annualization)
    return matrix


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_matrix_csv(path: Path, row_names: list[str], columns: list[str], matrix: np.ndarray) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["asset_id"] + columns)
        for i, row_name in enumerate(row_names):
            writer.writerow([row_name] + [round(float(value), 8) for value in matrix[i]])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    metadata_rows = [
        {
            "asset_id": asset["asset_id"],
            "ticker_or_series_id": asset["ticker"],
            "asset_name": asset["asset_name"],
            "asset_type": asset["asset_type"],
            "segment": asset["segment"],
            "quality_bucket": asset["quality_bucket"],
            "source": asset["source"],
        }
        for asset in ALL_ASSETS
    ]

    asset_daily_rows: list[dict[str, object]] = []
    asset_return_rows: list[dict[str, object]] = []
    monthly_return_rows: list[dict[str, object]] = []
    daily_returns_by_asset: dict[str, dict[str, float]] = {}
    monthly_returns_by_asset: dict[str, dict[str, float]] = {}

    for asset in ALL_ASSETS:
        asset_id = str(asset["asset_id"])
        levels = fetch_asset_levels(asset)
        daily_points = compute_period_returns(levels)
        month_points = compute_monthly_returns(month_end_rows(levels))

        daily_returns_by_asset[asset_id] = {}
        monthly_returns_by_asset[asset_id] = {}

        for obs_date, level, daily_return in daily_points:
            date_key = obs_date.isoformat()
            asset_daily_rows.append(
                {
                    "date": date_key,
                    "asset_id": asset_id,
                    "asset_name": asset["asset_name"],
                    "ticker_or_series_id": asset["ticker"],
                    "asset_type": asset["asset_type"],
                    "level": round(float(level), 6),
                }
            )
            asset_return_rows.append(
                {
                    "date": date_key,
                    "asset_id": asset_id,
                    "daily_return": round(float(daily_return), 8),
                }
            )
            daily_returns_by_asset[asset_id][date_key] = float(daily_return)

        for month_key, monthly_return in month_points:
            monthly_return_rows.append(
                {
                    "month": month_key,
                    "asset_id": asset_id,
                    "monthly_return": round(float(monthly_return), 8),
                }
            )
            monthly_returns_by_asset[asset_id][month_key] = float(monthly_return)

    factor_rows = build_factor_rows()
    asset_ids = [str(asset["asset_id"]) for asset in ALL_ASSETS]
    daily_cov = pairwise_covariance(daily_returns_by_asset, asset_ids, annualization=252.0)
    monthly_cov = pairwise_covariance(monthly_returns_by_asset, asset_ids, annualization=12.0)

    write_csv(
        DATA_DIR / "real_bond_asset_metadata.csv",
        [
            "asset_id",
            "ticker_or_series_id",
            "asset_name",
            "asset_type",
            "segment",
            "quality_bucket",
            "source",
        ],
        metadata_rows,
    )
    write_csv(
        DATA_DIR / "real_bond_assets_daily.csv",
        ["date", "asset_id", "asset_name", "ticker_or_series_id", "asset_type", "level"],
        asset_daily_rows,
    )
    write_csv(
        DATA_DIR / "real_bond_daily_returns.csv",
        ["date", "asset_id", "daily_return"],
        asset_return_rows,
    )
    write_csv(
        DATA_DIR / "real_bond_monthly_returns.csv",
        ["month", "asset_id", "monthly_return"],
        monthly_return_rows,
    )
    write_csv(
        DATA_DIR / "real_bond_factors_monthly.csv",
        [
            "date",
            "aaa_yield_pct",
            "baa_yield_pct",
            "treasury_2y_pct",
            "treasury_5y_pct",
            "treasury_10y_pct",
            "treasury_30y_pct",
            "corp_baa_aaa_spread_pct",
            "treasury_slope_10y_2y_pct",
        ],
        factor_rows,
    )
    write_matrix_csv(DATA_DIR / "real_bond_daily_covariance_matrix.csv", asset_ids, asset_ids, daily_cov)
    write_matrix_csv(
        DATA_DIR / "real_bond_monthly_covariance_matrix.csv", asset_ids, asset_ids, monthly_cov
    )
    write_csv(
        DATA_DIR / "real_dataset_manifest.csv",
        ["file_name", "row_count"],
        [
            {"file_name": "real_bond_asset_metadata.csv", "row_count": len(metadata_rows)},
            {"file_name": "real_bond_assets_daily.csv", "row_count": len(asset_daily_rows)},
            {"file_name": "real_bond_daily_returns.csv", "row_count": len(asset_return_rows)},
            {"file_name": "real_bond_monthly_returns.csv", "row_count": len(monthly_return_rows)},
            {"file_name": "real_bond_factors_monthly.csv", "row_count": len(factor_rows)},
            {"file_name": "real_bond_daily_covariance_matrix.csv", "row_count": len(asset_ids)},
            {"file_name": "real_bond_monthly_covariance_matrix.csv", "row_count": len(asset_ids)},
        ],
    )


if __name__ == "__main__":
    main()
