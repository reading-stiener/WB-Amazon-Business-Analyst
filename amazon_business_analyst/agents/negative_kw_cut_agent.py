"""Negative keyword CUT agent."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from amazon_business_analyst.config import AnalysisConfig
from amazon_business_analyst.metrics import safe_divide


@dataclass(frozen=True)
class NegativeKeywordResult:
    candidates: pd.DataFrame
    summary: pd.DataFrame
    metrics: dict[str, object]


class NegativeKeywordCutAgent:
    """Classify term-level spend into negative, review, and keep buckets."""

    def run(self, table: pd.DataFrame, config: AnalysisConfig) -> NegativeKeywordResult:
        grouped = (
            table.groupby("Customer Search Term Normalized", dropna=False)
            .agg(
                Spend=("Spend", "sum"),
                Sales=("Sales", "sum"),
                Orders=("Orders", "sum"),
                Clicks=("Clicks", "sum"),
                Impressions=("Impressions", "sum"),
            )
            .reset_index()
            .rename(columns={"Customer Search Term Normalized": "Customer Search Term"})
        )
        grouped["ACoS"] = safe_divide(grouped["Spend"], grouped["Sales"], infinity=True)
        grouped["CTR"] = safe_divide(grouped["Clicks"], grouped["Impressions"])
        grouped["CVR"] = safe_divide(grouped["Orders"], grouped["Clicks"])
        grouped["Classification"] = grouped.apply(lambda row: self._classify(row, config), axis=1)
        grouped["Reason"] = grouped["Classification"].map(
            {
                "INVALID: blank search term": "Blank search term cannot be uploaded as a negative",
                "NEGATIVE: zero orders": "No orders after spend threshold",
                "NEGATIVE: high ACoS": "ACoS above high-cost cutoff",
                "REVIEW": "High but not automatic-cut ACoS",
                "keep": "Below review threshold or insufficient spend",
            }
        )
        grouped = grouped.sort_values(["Classification", "Spend"], ascending=[True, False])

        summary = (
            grouped.groupby("Classification", dropna=False)
            .agg(Count=("Customer Search Term", "count"), Spend=("Spend", "sum"), Sales=("Sales", "sum"))
            .reset_index()
            .sort_values("Spend", ascending=False)
        )
        is_negative = grouped["Classification"].str.startswith("NEGATIVE")
        metrics = {
            "negative_candidate_count": int(is_negative.sum()),
            "review_candidate_count": int((grouped["Classification"] == "REVIEW").sum()),
            "recoverable_spend": float(grouped.loc[is_negative, "Spend"].sum()),
        }
        return NegativeKeywordResult(candidates=grouped, summary=summary, metrics=metrics)

    def _classify(self, row: pd.Series, config: AnalysisConfig) -> str:
        if row["Customer Search Term"] == "":
            return "INVALID: blank search term"
        if row["Orders"] == 0 and row["Spend"] >= config.neg_zero_order_min_spend:
            return "NEGATIVE: zero orders"
        if row["Spend"] >= config.neg_high_acos_min_spend and row["ACoS"] >= config.high_acos_cutoff:
            return "NEGATIVE: high ACoS"
        if (
            row["Spend"] >= config.neg_high_acos_min_spend
            and config.review_band_min <= row["ACoS"] < config.review_band_max
        ):
            return "REVIEW"
        return "keep"
