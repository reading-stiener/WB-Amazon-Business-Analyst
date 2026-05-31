"""Campaign enrichment agent."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from amazon_business_analyst.metrics import safe_divide


@dataclass(frozen=True)
class CampaignEnrichmentResult:
    table: pd.DataFrame
    report: dict[str, object]


class CampaignEnrichmentAgent:
    """Add campaign metadata and recompute trusted weighted metrics."""

    TARGETING_MARKERS = [
        (" - Auto - ", "Auto"),
        (" - Disc KW - ", "Disc KW"),
        (" - Conv KW - ", "Conv KW"),
        (" - Conq PAT - ", "Conq PAT"),
        (" - Def PAT - ", "Def PAT"),
    ]

    def run(self, table: pd.DataFrame) -> CampaignEnrichmentResult:
        enriched = table.copy()

        enriched["ACoS Exported"] = enriched["ACoS"]
        enriched["CTR Exported"] = enriched["CTR"]
        enriched["CVR Exported"] = enriched["CVR"]

        enriched["Customer Search Term Normalized"] = (
            enriched["Customer Search Term"].astype("string").fillna("").str.strip().str.lower()
        )
        enriched["Campaign Name Normalized"] = enriched["Campaign Name"].astype("string").fillna("").str.strip()
        enriched["Match Type"] = enriched["Match Type"].astype("string").fillna("").str.strip().str.upper()
        enriched["Targeting type"] = enriched["Campaign Name"].apply(self._targeting_type)
        enriched["Bucket"] = enriched["Customer Search Term Normalized"].apply(self._bucket)
        self._add_period_columns(enriched)

        enriched["ACoS"] = safe_divide(enriched["Spend"], enriched["Sales"], infinity=True)
        enriched["ROAS"] = safe_divide(enriched["Sales"], enriched["Spend"], infinity=True)
        enriched["CTR"] = safe_divide(enriched["Clicks"], enriched["Impressions"])
        enriched["CVR"] = safe_divide(enriched["Orders"], enriched["Clicks"])

        flags = []
        for _, row in enriched.iterrows():
            row_flags = []
            if row["Campaign Name Normalized"] == "":
                row_flags.append("blank_campaign")
            if row["Targeting type"] == "Other":
                row_flags.append("unknown_targeting_type")
            flags.append(";".join(row_flags))
        enriched["Validation Flags"] = flags

        report = {
            "targeting_type_counts": enriched["Targeting type"].value_counts(dropna=False).to_dict(),
            "bucket_counts": enriched["Bucket"].value_counts(dropna=False).to_dict(),
            "other_campaign_count": int((enriched["Targeting type"] == "Other").sum()),
        }
        return CampaignEnrichmentResult(table=enriched, report=report)

    def _targeting_type(self, campaign_name: object) -> str:
        text = str(campaign_name)
        for marker, targeting_type in self.TARGETING_MARKERS:
            if marker in text:
                return targeting_type
        return "Other"

    def _bucket(self, normalized_search_term: object) -> str:
        term = str(normalized_search_term).strip().upper()
        return "Brand Defense" if term.startswith("B0") else "Discovery"

    def _add_period_columns(self, enriched: pd.DataFrame) -> None:
        if "Start Date" not in enriched:
            enriched["Analysis Period Id"] = "current"
            enriched["Analysis Period Label"] = "Current period"
            enriched["Analysis Period Start"] = pd.NaT
            enriched["Analysis Period End"] = pd.NaT
            return

        start = pd.to_datetime(enriched["Start Date"], errors="coerce")
        end = pd.to_datetime(enriched["End Date"], errors="coerce") if "End Date" in enriched else start
        end = end.fillna(start)
        weekly_start = start.dt.to_period("W-SUN").dt.start_time
        weekly_end = weekly_start + pd.Timedelta(days=6)
        span_days = (end - start).dt.days.fillna(0)
        use_report_range = span_days > 7
        period_start = weekly_start.where(~use_report_range, start)
        period_end = weekly_end.where(~use_report_range, end)

        missing = period_start.isna()
        enriched["Analysis Period Start"] = period_start
        enriched["Analysis Period End"] = period_end
        enriched["Analysis Period Id"] = [
            "current" if is_missing else f"{period_start_value:%Y-%m-%d}_{period_end_value:%Y-%m-%d}"
            for is_missing, period_start_value, period_end_value in zip(missing, period_start, period_end)
        ]
        enriched["Analysis Period Label"] = [
            "Current period" if is_missing else self._format_period_label(period_start_value, period_end_value)
            for is_missing, period_start_value, period_end_value in zip(missing, period_start, period_end)
        ]

    def _format_period_label(self, start: pd.Timestamp, end: pd.Timestamp) -> str:
        if (end - start).days <= 6:
            return f"Week of {start:%b %-d, %Y}"
        if start.year == end.year:
            return f"{start:%b %-d} - {end:%b %-d, %Y}"
        return f"{start:%b %-d, %Y} - {end:%b %-d, %Y}"
