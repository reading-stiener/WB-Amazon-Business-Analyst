"""Harvest GROW agent."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from amazon_business_analyst.config import AnalysisConfig
from amazon_business_analyst.metrics import safe_divide


@dataclass(frozen=True)
class HarvestGrowResult:
    candidates: pd.DataFrame
    summary: dict[str, object]
    self_checks: dict[str, bool]


class HarvestGrowAgent:
    """Find discovery terms ready for exact-match conversion campaigns."""

    def run(self, table: pd.DataFrame, config: AnalysisConfig) -> HarvestGrowResult:
        grouped = (
            table.groupby("Customer Search Term Normalized", dropna=False)
            .agg(
                Orders=("Orders", "sum"),
                Spend=("Spend", "sum"),
                Sales=("Sales", "sum"),
                Clicks=("Clicks", "sum"),
                Impressions=("Impressions", "sum"),
            )
            .reset_index()
            .rename(columns={"Customer Search Term Normalized": "Customer Search Term"})
        )
        grouped["ACoS"] = safe_divide(grouped["Spend"], grouped["Sales"], infinity=True)
        grouped["CTR"] = safe_divide(grouped["Clicks"], grouped["Impressions"])
        grouped["CVR"] = safe_divide(grouped["Orders"], grouped["Clicks"])

        source_clicks = (
            table[table["Targeting type"].isin(["Auto", "Disc KW"])]
            .groupby("Customer Search Term Normalized")["Clicks"]
            .sum()
            .rename("clicks_in_auto_disc")
        )
        exact_clicks = (
            table[(table["Targeting type"] == "Conv KW") & (table["Match Type"] == "EXACT")]
            .groupby("Customer Search Term Normalized")["Clicks"]
            .sum()
            .rename("clicks_in_conv_exact")
        )

        candidates = grouped[
            (grouped["Orders"] >= config.harvest_min_orders)
            & (grouped["ACoS"] < config.harvest_max_acos)
            & (grouped["Customer Search Term"] != "")
        ].copy()
        candidates = candidates.merge(source_clicks, left_on="Customer Search Term", right_index=True, how="left")
        candidates = candidates.merge(exact_clicks, left_on="Customer Search Term", right_index=True, how="left")
        candidates[["clicks_in_auto_disc", "clicks_in_conv_exact"]] = candidates[
            ["clicks_in_auto_disc", "clicks_in_conv_exact"]
        ].fillna(0)
        candidates["Verdict"] = candidates.apply(self._verdict, axis=1)
        candidates = candidates.sort_values(["Verdict", "Sales"], ascending=[True, False])

        harvest = candidates[candidates["Verdict"] == "HARVEST -> promote to Conv KW exact"]
        weighted_acos = safe_divide(float(harvest["Spend"].sum()), float(harvest["Sales"].sum()), infinity=True)
        harvest_check = bool(
            (
                (harvest["clicks_in_auto_disc"] > 0)
                & (harvest["clicks_in_conv_exact"] == 0)
            ).all()
        )
        if not harvest_check:
            raise AssertionError("Harvest self-check failed: HARVEST rows have invalid source/exact coverage")

        summary = {
            "harvest_candidate_count": int(len(harvest)),
            "already_covered_count": int((candidates["Verdict"] == "Already covered").sum()),
            "outside_source_count": int((candidates["Verdict"] == "Outside harvest source").sum()),
            "harvest_sales": float(harvest["Sales"].sum()),
            "harvest_orders": float(harvest["Orders"].sum()),
            "harvest_weighted_acos": float(weighted_acos),
        }
        return HarvestGrowResult(candidates=candidates, summary=summary, self_checks={"harvest_rows_valid": harvest_check})

    def _verdict(self, row: pd.Series) -> str:
        if row["clicks_in_auto_disc"] > 0 and row["clicks_in_conv_exact"] == 0:
            return "HARVEST -> promote to Conv KW exact"
        if row["clicks_in_conv_exact"] > 0:
            return "Already covered"
        return "Outside harvest source"
