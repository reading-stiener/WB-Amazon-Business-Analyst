"""Input/output helpers for monthly Amazon search-term reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def load_source_table(path: str | Path, sheet_name: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    source_path = Path(path).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {source_path}")

    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source_path), {"path": str(source_path), "type": "csv", "sheet": None}

    if suffix in {".xlsx", ".xlsm", ".xls"}:
        excel = pd.ExcelFile(source_path)
        selected_sheet = sheet_name
        if selected_sheet is None:
            selected_sheet = "Data" if "Data" in excel.sheet_names else excel.sheet_names[0]
        if selected_sheet not in excel.sheet_names:
            raise ValueError(
                f"Sheet '{selected_sheet}' not found in {source_path}. "
                f"Available sheets: {', '.join(excel.sheet_names)}"
            )
        return (
            pd.read_excel(source_path, sheet_name=selected_sheet),
            {"path": str(source_path), "type": suffix.lstrip("."), "sheet": selected_sheet},
        )

    raise ValueError(f"Unsupported input file type: {suffix}. Use CSV or Excel.")


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = Path(path).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
