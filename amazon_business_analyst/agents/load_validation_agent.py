"""Load and validation agent."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from amazon_business_analyst.io import load_source_table
from amazon_business_analyst.metrics import coerce_numeric
from amazon_business_analyst.schemas import (
    COLUMN_ALIASES,
    NUMERIC_REQUIRED_COLUMNS,
    OPTIONAL_DATE_COLUMNS,
    RAW_METRIC_COLUMNS,
    REQUIRED_COLUMNS,
    TEXT_COLUMNS,
    normalize_header,
)


@dataclass(frozen=True)
class LoadValidationResult:
    table: pd.DataFrame
    report: dict[str, object]


class LoadValidationAgent:
    """Load raw CSV/XLSX data and produce the canonical 11-column table."""

    def run(self, input_path: str, sheet_name: str | None = None) -> LoadValidationResult:
        raw, source_info = load_source_table(input_path, sheet_name)
        raw.columns = [normalize_header(col) for col in raw.columns]

        canonical = pd.DataFrame(index=raw.index)
        source_columns: dict[str, str] = {}
        for raw_col in raw.columns:
            if raw_col.startswith("Unnamed:"):
                continue
            canonical_name = COLUMN_ALIASES.get(raw_col)
            if canonical_name and canonical_name not in canonical:
                canonical[canonical_name] = raw[raw_col]
                source_columns[canonical_name] = raw_col

        missing = [column for column in REQUIRED_COLUMNS if column not in canonical]
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(missing)}")

        canonical_columns = REQUIRED_COLUMNS + [column for column in OPTIONAL_DATE_COLUMNS if column in canonical]
        canonical = canonical.loc[:, canonical_columns].copy()

        for column in TEXT_COLUMNS:
            canonical[column] = canonical[column].astype("string").fillna("").str.strip()

        blank_campaign_count = int((canonical["Campaign Name"] == "").sum())
        blank_search_term_count = int((canonical["Customer Search Term"] == "").sum())

        numeric_errors = 0
        for column in NUMERIC_REQUIRED_COLUMNS:
            before_non_blank = canonical[column].notna() & (canonical[column].astype("string").str.strip() != "")
            numeric = coerce_numeric(canonical[column])
            numeric_errors += int((before_non_blank & numeric.isna()).sum())
            canonical[column] = numeric

        if numeric_errors:
            raise ValueError(f"Numeric coercion failed for {numeric_errors} required value(s)")

        for column in RAW_METRIC_COLUMNS:
            canonical[column] = coerce_numeric(canonical[column])

        date_parse_error_count = 0
        for column in OPTIONAL_DATE_COLUMNS:
            if column not in canonical:
                continue
            before_non_blank = canonical[column].notna() & (canonical[column].astype("string").str.strip() != "")
            parsed = pd.to_datetime(canonical[column], errors="coerce")
            date_parse_error_count += int((before_non_blank & parsed.isna()).sum())
            canonical[column] = parsed

        report = {
            "source": source_info,
            "raw_column_count": int(len(raw.columns)),
            "row_count": int(len(canonical)),
            "blank_campaign_count": blank_campaign_count,
            "blank_search_term_count": blank_search_term_count,
            "numeric_coercion_error_count": numeric_errors,
            "date_parse_error_count": date_parse_error_count,
            "source_columns": source_columns,
        }
        return LoadValidationResult(table=canonical, report=report)
