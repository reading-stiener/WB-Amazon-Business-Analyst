"""Recommendation report writer agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from amazon_business_analyst.config import AnalysisConfig
from amazon_business_analyst.metrics import markdown_table, money, percent


@dataclass(frozen=True)
class RecommendationWriterResult:
    report_path: Path


class RecommendationWriterAgent:
    """Write the final CUT/FIX/GROW markdown report."""

    def run(
        self,
        output_dir: Path,
        config: AnalysisConfig,
        scorecard: pd.DataFrame,
        scorecard_narrative: str,
        negative_candidates: pd.DataFrame,
        harvest_candidates: pd.DataFrame,
    ) -> RecommendationWriterResult:
        blended = scorecard[scorecard["Bucket"] == "Blended"].iloc[0]
        negative_rows = negative_candidates[
            negative_candidates["Classification"].str.startswith("NEGATIVE")
        ].sort_values("Spend", ascending=False)
        review_rows = negative_candidates[negative_candidates["Classification"] == "REVIEW"].sort_values(
            "Spend", ascending=False
        )
        harvest_rows = harvest_candidates[
            harvest_candidates["Verdict"] == "HARVEST -> promote to Conv KW exact"
        ].sort_values("Sales", ascending=False)

        spend_ceiling = float(blended["Sales"]) * config.target_acos_blended
        sales_floor = float(blended["Spend"]) / config.target_acos_blended if config.target_acos_blended else 0.0
        recoverable_spend = float(negative_rows["Spend"].sum())
        harvest_sales = float(harvest_rows["Sales"].sum())
        harvest_orders = float(harvest_rows["Orders"].sum())
        harvest_acos = float(harvest_rows["Spend"].sum() / harvest_rows["Sales"].sum()) if harvest_sales else 0.0

        report = [
            "# Next Month Amazon Search-Term Recommendations",
            "",
            "## Executive Summary",
            "",
            scorecard_narrative,
            "",
            f"- CUT opportunity: {len(negative_rows):,} negative keyword candidates with "
            f"{money(recoverable_spend)} in recoverable spend.",
            f"- FIX queue: {len(review_rows):,} review terms need bid, copy, landing page, or relevance checks.",
            f"- GROW queue: {len(harvest_rows):,} harvest terms generated {money(harvest_sales)} "
            f"from {harvest_orders:,.0f} orders at {percent(harvest_acos)} weighted ACoS.",
            "",
            "## Scorecard",
            "",
            markdown_table(
                self._format_scorecard(scorecard),
                ["Bucket", "Spend", "Sales", "Orders", "ACoS", "Target ACoS", "Dollar Over Target"],
                config.report_max_rows,
            ),
            "",
            "## CUT: Negative Keyword Candidates",
            "",
            markdown_table(
                self._format_action_rows(negative_rows),
                ["Customer Search Term", "Classification", "Reason", "Spend", "Sales", "Orders", "ACoS"],
                config.report_max_rows,
            ),
            "",
            "## FIX: Review and Bid-Cut Candidates",
            "",
            "Review terms are not automatic negatives. Start with bid reductions, campaign isolation, "
            "query relevance checks, or listing-message fixes before cutting traffic.",
            "",
            markdown_table(
                self._format_action_rows(review_rows),
                ["Customer Search Term", "Classification", "Reason", "Spend", "Sales", "Orders", "ACoS"],
                config.report_max_rows,
            ),
            "",
            "## GROW: Harvest Candidates",
            "",
            markdown_table(
                self._format_harvest_rows(harvest_rows),
                [
                    "Customer Search Term",
                    "Verdict",
                    "Spend",
                    "Sales",
                    "Orders",
                    "ACoS",
                    "clicks_in_auto_disc",
                    "clicks_in_conv_exact",
                ],
                config.report_max_rows,
            ),
            "",
            "## Next-Month Targets",
            "",
            f"- Spend ceiling at current sales: {money(spend_ceiling)} "
            f"({money(float(blended['Sales']))} sales x {percent(config.target_acos_blended)} target ACoS).",
            f"- Sales floor at current spend: {money(sales_floor)} "
            f"({money(float(blended['Spend']))} spend / {percent(config.target_acos_blended)} target ACoS).",
            f"- Blended ACoS target: {percent(config.target_acos_blended)}.",
            f"- Profitable-sales target: at least {money(sales_floor)} if spend remains near "
            f"{money(float(blended['Spend']))}.",
            "",
            "## Caveats and Checks",
            "",
            "- Bid cuts can reduce sales before efficiency improves.",
            "- Thresholds should be swept in W&B or the local artifact manifest before production automation.",
            "- CUT and GROW sets should be checked for overlap before uploading changes to Amazon Ads.",
            "- Recent rows can be affected by attribution lag, inventory changes, and listing edits.",
            "",
        ]

        report_path = output_dir / "next_month_recommendations.md"
        report_path.write_text("\n".join(report), encoding="utf-8")
        return RecommendationWriterResult(report_path=report_path)

    def _format_scorecard(self, scorecard: pd.DataFrame) -> pd.DataFrame:
        formatted = scorecard.copy()
        for column in ["Spend", "Sales", "Dollar Over Target"]:
            formatted[column] = formatted[column].map(lambda value: money(float(value)))
        formatted["Orders"] = formatted["Orders"].map(lambda value: f"{float(value):,.0f}")
        for column in ["ACoS", "Target ACoS"]:
            formatted[column] = formatted[column].map(lambda value: percent(float(value)))
        return formatted

    def _format_action_rows(self, rows: pd.DataFrame) -> pd.DataFrame:
        formatted = rows.copy()
        for column in ["Spend", "Sales"]:
            formatted[column] = formatted[column].map(lambda value: money(float(value)))
        formatted["Orders"] = formatted["Orders"].map(lambda value: f"{float(value):,.0f}")
        formatted["ACoS"] = formatted["ACoS"].map(lambda value: percent(float(value)))
        return formatted

    def _format_harvest_rows(self, rows: pd.DataFrame) -> pd.DataFrame:
        formatted = rows.copy()
        for column in ["Spend", "Sales"]:
            formatted[column] = formatted[column].map(lambda value: money(float(value)))
        formatted["Orders"] = formatted["Orders"].map(lambda value: f"{float(value):,.0f}")
        formatted["ACoS"] = formatted["ACoS"].map(lambda value: percent(float(value)))
        formatted["clicks_in_auto_disc"] = formatted["clicks_in_auto_disc"].map(lambda value: f"{float(value):,.0f}")
        formatted["clicks_in_conv_exact"] = formatted["clicks_in_conv_exact"].map(lambda value: f"{float(value):,.0f}")
        return formatted
