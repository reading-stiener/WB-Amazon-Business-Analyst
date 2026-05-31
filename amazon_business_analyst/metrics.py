"""Metric and formatting helpers shared by agents."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def coerce_numeric(series: pd.Series) -> pd.Series:
    """Convert Amazon export number strings into floats.

    Handles currency symbols, commas, blanks, percentages, and already-numeric
    values. Percent strings are converted to decimal rates.
    """

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    raw = series.astype("string")
    has_percent = raw.str.contains("%", regex=False, na=False)
    cleaned = (
        raw.str.strip()
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace({"": pd.NA, "-": pd.NA})
    )
    numeric = pd.to_numeric(cleaned, errors="coerce")
    numeric.loc[has_percent] = numeric.loc[has_percent] / 100.0
    return numeric


def safe_divide(numerator: pd.Series | float, denominator: pd.Series | float, *, infinity: bool = False) -> Any:
    """Divide while avoiding NaN/inf surprises for reporting metrics."""

    if isinstance(numerator, pd.Series) or isinstance(denominator, pd.Series):
        num = pd.Series(numerator)
        den = pd.Series(denominator)
        with np.errstate(divide="ignore", invalid="ignore"):
            result = num / den
        result = result.where(den != 0, np.inf if infinity else 0.0)
        result = result.fillna(0.0)
        return result

    if denominator == 0:
        return math.inf if infinity and numerator > 0 else 0.0
    return numerator / denominator


def weighted_metrics(frame: pd.DataFrame) -> dict[str, float]:
    spend = float(frame["Spend"].sum())
    sales = float(frame["Sales"].sum())
    clicks = float(frame["Clicks"].sum())
    impressions = float(frame["Impressions"].sum())
    orders = float(frame["Orders"].sum())
    return {
        "Spend": spend,
        "Sales": sales,
        "Orders": orders,
        "Clicks": clicks,
        "Impressions": impressions,
        "ACoS": safe_divide(spend, sales, infinity=True),
        "ROAS": safe_divide(sales, spend, infinity=True),
        "CTR": safe_divide(clicks, impressions),
        "CVR": safe_divide(orders, clicks),
    }


def finite_float(value: float) -> float | str:
    if isinstance(value, (int, float)) and math.isinf(value):
        return "Infinity"
    return float(value)


def money(value: float) -> str:
    return f"${value:,.2f}"


def percent(value: float) -> str:
    if isinstance(value, (int, float)) and math.isinf(value):
        return "Infinity"
    return f"{value:.2%}"


def markdown_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int) -> str:
    visible = frame.loc[:, columns].head(max_rows).copy()
    if visible.empty:
        return "_No rows._"

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in visible.iterrows():
        rows.append("| " + " | ".join(markdown_escape(row[col]) for col in columns) + " |")
    suffix = ""
    if len(frame) > max_rows:
        suffix = f"\n\n_Showing top {max_rows:,} of {len(frame):,} rows. See CSV artifact for the full list._"
    return "\n".join([header, separator, *rows]) + suffix
