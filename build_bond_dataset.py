from __future__ import annotations

import csv
import io
import math
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np


START_DATE = date.fromisoformat("2016-01-01")
END_DATE = date.fromisoformat("2025-12-01")
RNG = np.random.default_rng(1019)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

FRED_SERIES = {
    "aaa_yield_pct": "AAA",
    "baa_yield_pct": "BAA",
    "treasury_1y_pct": "GS1",
    "treasury_2y_pct": "GS2",
    "treasury_5y_pct": "GS5",
    "treasury_10y_pct": "GS10",
    "treasury_20y_pct": "GS20",
    "treasury_30y_pct": "GS30",
}

US_STATES = [
    "CA",
    "NY",
    "TX",
    "FL",
    "IL",
    "PA",
    "OH",
    "NC",
    "GA",
    "WA",
    "MA",
    "NJ",
]

FOREIGN_MARKETS = ["Canada", "Germany", "United Kingdom", "Japan", "Australia", "Mexico"]


def fetch_fred_series(series_id: str) -> list[tuple[date, float | None]]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urllib.request.urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    rows: list[tuple[date, float | None]] = []
    for row in reader:
        value = row[series_id]
        parsed = None if value in {"", "."} else float(value)
        rows.append((date.fromisoformat(row["observation_date"]), parsed))
    return rows


def fill_missing(values: np.ndarray) -> np.ndarray:
    result = values.copy()
    last = np.nan
    for i in range(len(result)):
        if np.isnan(result[i]):
            if not np.isnan(last):
                result[i] = last
        else:
            last = result[i]
    last = np.nan
    for i in range(len(result) - 1, -1, -1):
        if np.isnan(result[i]):
            if not np.isnan(last):
                result[i] = last
        else:
            last = result[i]
    return np.nan_to_num(result, nan=0.0)


def rolling_std(values: np.ndarray, window: int) -> np.ndarray:
    out = np.zeros_like(values)
    for i in range(window - 1, len(values)):
        sample = values[i - window + 1 : i + 1]
        out[i] = float(np.std(sample, ddof=1)) if window > 1 else 0.0
    return out


def build_factor_dataset() -> tuple[list[date], dict[str, np.ndarray]]:
    merged: dict[date, dict[str, float | None]] = {}
    for column_name, series_id in FRED_SERIES.items():
        for obs_date, value in fetch_fred_series(series_id):
            if START_DATE <= obs_date <= END_DATE:
                merged.setdefault(obs_date, {})[column_name] = value

    dates = sorted(merged)
    data: dict[str, np.ndarray] = {}
    for column_name in FRED_SERIES:
        arr = np.array([merged[obs_date].get(column_name, np.nan) for obs_date in dates], dtype=float)
        data[column_name] = fill_missing(arr)

    treasury_cols = [name for name in data if name.startswith("treasury_")]
    treasury_stack = np.column_stack([data[name] for name in treasury_cols])
    data["avg_treasury_curve_pct"] = np.mean(treasury_stack, axis=1)
    data["corp_aaa_spread_pct"] = data["aaa_yield_pct"] - data["treasury_10y_pct"]
    data["corp_baa_spread_pct"] = data["baa_yield_pct"] - data["treasury_10y_pct"]
    data["corp_baa_aaa_spread_pct"] = data["baa_yield_pct"] - data["aaa_yield_pct"]
    data["treasury_slope_10y_2y_pct"] = data["treasury_10y_pct"] - data["treasury_2y_pct"]
    data["treasury_slope_30y_10y_pct"] = data["treasury_30y_pct"] - data["treasury_10y_pct"]
    data["monthly_change_t10_pct"] = np.diff(data["treasury_10y_pct"], prepend=data["treasury_10y_pct"][0])
    data["monthly_change_aaa_spread_pct"] = np.diff(
        data["corp_aaa_spread_pct"], prepend=data["corp_aaa_spread_pct"][0]
    )
    data["monthly_change_baa_spread_pct"] = np.diff(
        data["corp_baa_spread_pct"], prepend=data["corp_baa_spread_pct"][0]
    )
    data["rate_vol_3m_pct"] = rolling_std(data["monthly_change_t10_pct"], window=3)
    data["spread_vol_3m_pct"] = rolling_std(data["monthly_change_baa_spread_pct"], window=3)
    return dates, data


def _sample_range(low: float, high: float) -> float:
    return float(RNG.uniform(low, high))


def build_bond_universe(latest: dict[str, float], n_bonds: int = 500) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    mix = [
        ("treasury", 120),
        ("corporate", 190),
        ("municipal", 110),
        ("foreign", 80),
    ]

    bond_index = 1
    for bond_type, count in mix:
        for _ in range(count):
            if bond_index > n_bonds:
                break

            rating = ""
            region = "US"
            tax_status = "taxable"
            liquidity = 0.0
            duration = 0.0
            maturity = 0.0
            spread = 0.0
            level_beta = 0.0
            slope_beta = 0.0
            spread_ig_beta = 0.0
            spread_hy_beta = 0.0
            muni_beta = 0.0
            fx_beta = 0.0
            face_value = int(RNG.choice([1000, 5000, 10000, 25000]))

            if bond_type == "treasury":
                rating = "AAA"
                maturity = _sample_range(1.5, 28.0)
                duration = maturity * _sample_range(0.75, 0.92)
                spread = _sample_range(-0.15, 0.10)
                liquidity = _sample_range(0.90, 0.99)
                level_beta = _sample_range(0.90, 1.05)
                slope_beta = _sample_range(0.15, 0.45)
            elif bond_type == "corporate":
                rating = str(RNG.choice(["AAA", "AA", "A", "BBB", "BB"]))
                maturity = _sample_range(2.0, 20.0)
                duration = maturity * _sample_range(0.65, 0.90)
                spread_map = {
                    "AAA": _sample_range(0.10, 0.50),
                    "AA": _sample_range(0.35, 0.85),
                    "A": _sample_range(0.75, 1.40),
                    "BBB": _sample_range(1.30, 2.40),
                    "BB": _sample_range(2.10, 3.80),
                }
                spread = spread_map[rating]
                liquidity = _sample_range(0.45, 0.90)
                level_beta = _sample_range(0.75, 1.05)
                slope_beta = _sample_range(0.05, 0.35)
                if rating in {"AAA", "AA", "A"}:
                    spread_ig_beta = _sample_range(0.70, 1.20)
                    spread_hy_beta = _sample_range(0.05, 0.20)
                else:
                    spread_ig_beta = _sample_range(0.40, 0.90)
                    spread_hy_beta = _sample_range(0.70, 1.25)
            elif bond_type == "municipal":
                rating = str(RNG.choice(["AA", "A", "BBB"]))
                maturity = _sample_range(3.0, 25.0)
                duration = maturity * _sample_range(0.70, 0.94)
                spread_map = {
                    "AA": _sample_range(0.25, 0.90),
                    "A": _sample_range(0.70, 1.50),
                    "BBB": _sample_range(1.30, 2.10),
                }
                spread = spread_map[rating]
                liquidity = _sample_range(0.35, 0.78)
                level_beta = _sample_range(0.65, 0.98)
                slope_beta = _sample_range(0.04, 0.25)
                muni_beta = _sample_range(0.60, 1.15)
                region = str(RNG.choice(US_STATES))
                tax_status = "tax_exempt"
            else:
                rating = str(RNG.choice(["AA", "A", "BBB", "BB"]))
                maturity = _sample_range(2.0, 18.0)
                duration = maturity * _sample_range(0.60, 0.88)
                spread_map = {
                    "AA": _sample_range(0.45, 1.10),
                    "A": _sample_range(0.90, 1.70),
                    "BBB": _sample_range(1.60, 2.80),
                    "BB": _sample_range(2.70, 4.25),
                }
                spread = spread_map[rating]
                liquidity = _sample_range(0.30, 0.72)
                level_beta = _sample_range(0.70, 1.05)
                slope_beta = _sample_range(-0.05, 0.25)
                spread_ig_beta = _sample_range(0.20, 0.80)
                spread_hy_beta = _sample_range(0.35, 1.10)
                fx_beta = _sample_range(0.20, 0.85)
                region = str(RNG.choice(FOREIGN_MARKETS))

            base_curve = float(
                np.interp(
                    maturity,
                    [1, 2, 5, 10, 20, 30],
                    [
                        latest["treasury_1y_pct"],
                        latest["treasury_2y_pct"],
                        latest["treasury_5y_pct"],
                        latest["treasury_10y_pct"],
                        latest["treasury_20y_pct"],
                        latest["treasury_30y_pct"],
                    ],
                )
            )
            liquidity_penalty = (1.0 - liquidity) * 0.45
            yield_to_worst = base_curve + spread + liquidity_penalty
            coupon_rate = max(0.25, yield_to_worst + _sample_range(-0.75, 0.75))
            price = 100 + _sample_range(-12.0, 12.0)
            annual_volatility = (
                1.8
                + 0.18 * duration
                + 1.3 * spread_ig_beta
                + 1.8 * spread_hy_beta
                + 1.4 * muni_beta
                + 1.8 * fx_beta
                + (1.0 - liquidity) * 4.0
            )
            expected_return = yield_to_worst - 0.12 * annual_volatility

            records.append(
                {
                    "bond_id": f"BOND_{bond_index:04d}",
                    "bond_type": bond_type,
                    "rating_bucket": rating,
                    "region": region,
                    "tax_status": tax_status,
                    "face_value": face_value,
                    "minimum_increment": face_value,
                    "maturity_years": round(maturity, 2),
                    "duration_years": round(duration, 2),
                    "coupon_rate_pct": round(coupon_rate, 3),
                    "market_price": round(price, 2),
                    "yield_to_worst_pct": round(yield_to_worst, 3),
                    "expected_annual_return_pct": round(expected_return, 3),
                    "annual_volatility_pct": round(annual_volatility, 3),
                    "liquidity_score": round(liquidity, 3),
                    "level_beta": round(level_beta, 3),
                    "slope_beta": round(slope_beta, 3),
                    "spread_ig_beta": round(spread_ig_beta, 3),
                    "spread_hy_beta": round(spread_hy_beta, 3),
                    "muni_beta": round(muni_beta, 3),
                    "fx_beta": round(fx_beta, 3),
                }
            )
            bond_index += 1

    return records


def build_fx_factor(length: int) -> np.ndarray:
    shocks = RNG.normal(loc=0.0, scale=0.0035, size=length)
    process = np.zeros(length)
    for i in range(1, length):
        process[i] = 0.35 * process[i - 1] + shocks[i]
    return process


def build_bond_history(
    dates: list[date], factors: dict[str, np.ndarray], universe: list[dict[str, object]]
) -> tuple[list[dict[str, object]], np.ndarray]:
    level_move = np.diff(factors["treasury_10y_pct"], prepend=factors["treasury_10y_pct"][0]) / 100.0
    slope_move = np.diff(
        factors["treasury_slope_10y_2y_pct"], prepend=factors["treasury_slope_10y_2y_pct"][0]
    ) / 100.0
    ig_spread_move = np.diff(
        factors["corp_aaa_spread_pct"], prepend=factors["corp_aaa_spread_pct"][0]
    ) / 100.0
    hy_spread_move = np.diff(
        factors["corp_baa_spread_pct"], prepend=factors["corp_baa_spread_pct"][0]
    ) / 100.0
    muni_move = 0.7 * ig_spread_move + 0.3 * slope_move
    fx_move = build_fx_factor(len(dates))

    matrix = np.zeros((len(dates), len(universe)))
    rows: list[dict[str, object]] = []

    for j, bond in enumerate(universe):
        monthly_carry = max(0.0002, float(bond["yield_to_worst_pct"]) / 1200.0)
        idio_monthly_vol = max(
            0.001, float(bond["annual_volatility_pct"]) / 100.0 / math.sqrt(12.0) * 0.25
        )
        idio = RNG.normal(loc=0.0, scale=idio_monthly_vol, size=len(dates))
        total_return = (
            monthly_carry
            - float(bond["duration_years"])
            * (
                float(bond["level_beta"]) * level_move
                + 0.35 * float(bond["slope_beta"]) * slope_move
                + 0.20 * float(bond["spread_ig_beta"]) * ig_spread_move
                + 0.25 * float(bond["spread_hy_beta"]) * hy_spread_move
                + 0.20 * float(bond["muni_beta"]) * muni_move
            )
            + float(bond["fx_beta"]) * fx_move
            + idio
        )
        matrix[:, j] = total_return
        for i, obs_date in enumerate(dates):
            rows.append(
                {
                    "date": obs_date.isoformat(),
                    "bond_id": bond["bond_id"],
                    "bond_type": bond["bond_type"],
                    "rating_bucket": bond["rating_bucket"],
                    "monthly_total_return": round(float(total_return[i]), 6),
                }
            )

    return rows, matrix


def build_covariance_matrix(matrix: np.ndarray) -> np.ndarray:
    return np.cov(matrix, rowvar=False) * 12.0


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_factor_csv(path: Path, dates: list[date], data: dict[str, np.ndarray]) -> None:
    fieldnames = ["date"] + list(data.keys())
    rows: list[dict[str, object]] = []
    for i, obs_date in enumerate(dates):
        row: dict[str, object] = {"date": obs_date.isoformat()}
        for key, values in data.items():
            row[key] = round(float(values[i]), 6)
        rows.append(row)
    write_csv(path, fieldnames, rows)


def write_covariance_csv(path: Path, universe: list[dict[str, object]], covariance: np.ndarray) -> None:
    header = ["bond_id"] + [str(bond["bond_id"]) for bond in universe]
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for i, bond in enumerate(universe):
            writer.writerow([bond["bond_id"]] + [round(float(value), 8) for value in covariance[i]])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    dates, factors = build_factor_dataset()
    latest = {key: float(values[-1]) for key, values in factors.items()}
    universe = build_bond_universe(latest)
    history_rows, history_matrix = build_bond_history(dates, factors, universe)
    covariance = build_covariance_matrix(history_matrix)

    write_factor_csv(DATA_DIR / "bond_factors_monthly.csv", dates, factors)
    write_csv(DATA_DIR / "synthetic_bond_universe.csv", list(universe[0].keys()), universe)
    write_csv(
        DATA_DIR / "synthetic_bond_history.csv",
        ["date", "bond_id", "bond_type", "rating_bucket", "monthly_total_return"],
        history_rows,
    )
    write_covariance_csv(DATA_DIR / "synthetic_covariance_matrix.csv", universe, covariance)
    write_csv(
        DATA_DIR / "dataset_manifest.csv",
        ["file_name", "row_count"],
        [
            {"file_name": "bond_factors_monthly.csv", "row_count": len(dates)},
            {"file_name": "synthetic_bond_universe.csv", "row_count": len(universe)},
            {"file_name": "synthetic_bond_history.csv", "row_count": len(history_rows)},
            {"file_name": "synthetic_covariance_matrix.csv", "row_count": covariance.shape[0]},
        ],
    )


if __name__ == "__main__":
    main()
