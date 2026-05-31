"""Canonical schema and Amazon export column aliases."""

from __future__ import annotations

REQUIRED_COLUMNS = [
    "Customer Search Term",
    "Match Type",
    "Campaign Name",
    "Clicks",
    "Impressions",
    "Spend",
    "Orders",
    "Sales",
    "ACoS",
    "CVR",
    "CTR",
]

OPTIONAL_DATE_COLUMNS = ["Start Date", "End Date"]

TEXT_COLUMNS = ["Customer Search Term", "Match Type", "Campaign Name"]

NUMERIC_REQUIRED_COLUMNS = ["Clicks", "Impressions", "Spend", "Orders", "Sales"]

RAW_METRIC_COLUMNS = ["ACoS", "CVR", "CTR"]

COLUMN_ALIASES = {
    "Start Date": "Start Date",
    "End Date": "End Date",
    "Customer Search Term": "Customer Search Term",
    "Match Type": "Match Type",
    "Campaign Name": "Campaign Name",
    "Clicks": "Clicks",
    "Impressions": "Impressions",
    "Spend": "Spend",
    "Orders": "Orders",
    "7 Day Total Orders (#)": "Orders",
    "Sales": "Sales",
    "7 Day Total Sales": "Sales",
    "ACoS": "ACoS",
    "Total Advertising Cost of Sales (ACOS)": "ACoS",
    "CVR": "CVR",
    "7 Day Conversion Rate": "CVR",
    "CTR": "CTR",
    "Click-Thru Rate (CTR)": "CTR",
}


def normalize_header(header: object) -> str:
    return str(header).strip()
