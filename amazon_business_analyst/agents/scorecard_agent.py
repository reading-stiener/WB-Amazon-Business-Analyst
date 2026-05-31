"""Scorecard agent."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from amazon_business_analyst.config import AnalysisConfig
from amazon_business_analyst.metrics import weighted_metrics


@dataclass(frozen=True)
class ScorecardResult:
    scorecard: pd.DataFrame
    narrative: str
    metrics: dict[str, object]
    self_checks: dict[str, bool]


class ScorecardAgent:
    """Compute bucket and blended weighted performance against targets."""

    def run(self, table: pd.DataFrame, config: AnalysisConfig) -> ScorecardResult:
        rows = []
        for bucket, bucket_frame in table.groupby("Bucket", dropna=False):
            metrics = weighted_metrics(bucket_frame)
            target = (
                config.target_acos_brand
                if bucket == "Brand Defense"
                else config.target_acos_discovery
            )
            rows.append({"Bucket": bucket, **metrics, "Target ACoS": target})

        blended = weighted_metrics(table)
        rows.append({"Bucket": "Blended", **blended, "Target ACoS": config.target_acos_blended})

        scorecard = pd.DataFrame(rows)
        scorecard["Variance"] = scorecard["ACoS"] - scorecard["Target ACoS"]
        scorecard["Dollar Over Target"] = scorecard["Variance"] * scorecard["Sales"]

        bucket_rows = scorecard[scorecard["Bucket"] != "Blended"]
        blended_row = scorecard[scorecard["Bucket"] == "Blended"].iloc[0]
        spend_ties = math.isclose(float(blended_row["Spend"]), float(bucket_rows["Spend"].sum()), abs_tol=0.01)
        sales_ties = math.isclose(float(blended_row["Sales"]), float(bucket_rows["Sales"].sum()), abs_tol=0.01)

        if not spend_ties or not sales_ties:
            raise AssertionError("Scorecard self-check failed: blended totals do not tie to bucket totals")

        positive_overage = bucket_rows.copy()
        positive_overage["Positive Dollar Over Target"] = positive_overage["Dollar Over Target"].clip(lower=0)
        if positive_overage["Positive Dollar Over Target"].max() > 0:
            driver = positive_overage.sort_values("Positive Dollar Over Target", ascending=False).iloc[0]
        else:
            driver = bucket_rows.sort_values("Variance", ascending=False).iloc[0]

        total_overage = float(blended_row["Dollar Over Target"])
        narrative = (
            f"Blended ACoS was {float(blended_row['ACoS']):.2%} versus the "
            f"{float(blended_row['Target ACoS']):.2%} target. "
            f"The largest bucket driver was {driver['Bucket']} at {float(driver['ACoS']):.2%} "
            f"ACoS versus {float(driver['Target ACoS']):.2%} target. "
            f"Total dollar overage was ${total_overage:,.2f}."
        )

        metrics = {
            "blended_spend": float(blended_row["Spend"]),
            "blended_sales": float(blended_row["Sales"]),
            "blended_acos": float(blended_row["ACoS"]),
            "blended_target_acos": float(blended_row["Target ACoS"]),
            "dollar_over_target": total_overage,
            "driver_bucket": str(driver["Bucket"]),
        }
        return ScorecardResult(
            scorecard=scorecard,
            narrative=narrative,
            metrics=metrics,
            self_checks={"spend_ties": spend_ties, "sales_ties": sales_ties},
        )
