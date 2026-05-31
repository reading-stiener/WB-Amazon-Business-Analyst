"""Generate static dashboard data from pipeline artifacts."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from amazon_business_analyst.agents.harvest_grow_agent import HarvestGrowAgent
from amazon_business_analyst.agents.negative_kw_cut_agent import NegativeKeywordCutAgent
from amazon_business_analyst.agents.scorecard_agent import ScorecardAgent
from amazon_business_analyst.config import AnalysisConfig

DASHBOARD_ASSET_NAMES = ("index.html", "styles.css", "app.js")


def build_dashboard_data(run_dir: str | Path) -> dict[str, Any]:
    source = Path(run_dir).expanduser().resolve()
    summary = json.loads((source / "run_summary.json").read_text(encoding="utf-8"))
    scorecard = pd.read_csv(source / "scorecard.csv")
    negatives = pd.read_csv(source / "negative_keyword_candidates.csv").fillna("")
    harvest = pd.read_csv(source / "harvest_candidates.csv").fillna("")
    enriched = pd.read_csv(source / "enriched_search_terms.csv")
    config = AnalysisConfig.from_mapping(summary["config"])

    all_period = _build_period_payload(
        period_id="all",
        label="All available weeks",
        scorecard=scorecard,
        negatives=negatives,
        harvest=harvest,
        metrics=summary["metrics"],
        config=config,
    )

    weeks = _build_weekly_payloads(enriched, config)
    if not weeks:
        weeks = [all_period]
    current_period = weeks[0]

    data = {
        "source": {
            "period": current_period["label"],
            "brand": "PajamaGram",
            "input_path": summary["input_path"],
            "report_path": summary["report_path"],
        },
        "config": summary["config"],
        "weeks": weeks,
        "currentWeekId": current_period["id"],
        **current_period,
        "allPeriods": all_period,
    }
    return _json_safe(data)


def _build_weekly_payloads(enriched: pd.DataFrame, config: AnalysisConfig) -> list[dict[str, Any]]:
    if "Start Date" not in enriched:
        return []

    frame = enriched.copy()
    row_start = pd.to_datetime(frame["Start Date"], errors="coerce")
    row_end = pd.to_datetime(frame["End Date"], errors="coerce") if "End Date" in frame else row_start
    row_end = row_end.fillna(row_start)
    valid_dates = row_start.notna() & row_end.notna()
    if not bool(valid_dates.any()):
        return []

    frame = frame.loc[valid_dates].copy()
    row_start = row_start.loc[valid_dates].dt.normalize()
    row_end = row_end.loc[valid_dates].dt.normalize()
    report_start = row_start.min()
    report_end = row_end.max()

    payloads = []
    current_start = report_start
    week_index = 1
    while current_start <= report_end:
        current_end = min(current_start + pd.Timedelta(days=6), report_end)
        period_frame, estimated = _slice_period_frame(frame, row_start, row_end, current_start, current_end)
        if period_frame.empty:
            current_start = current_end + pd.Timedelta(days=1)
            week_index += 1
            continue
        period_id = f"{current_start:%Y-%m-%d}_{current_end:%Y-%m-%d}"
        label = _format_week_label(week_index, current_start, current_end)
        scorecard_result = ScorecardAgent().run(period_frame, config)
        cut_result = NegativeKeywordCutAgent().run(period_frame, config)
        grow_result = HarvestGrowAgent().run(period_frame, config)
        metrics = {
            **scorecard_result.metrics,
            **cut_result.metrics,
            **grow_result.summary,
        }
        for _, scorecard_row in scorecard_result.scorecard.iterrows():
            bucket_key = str(scorecard_row["Bucket"]).lower().replace(" ", "_")
            if bucket_key == "blended":
                continue
            metrics[f"{bucket_key}_spend"] = float(scorecard_row["Spend"])
            metrics[f"{bucket_key}_sales"] = float(scorecard_row["Sales"])
            metrics[f"{bucket_key}_acos"] = float(scorecard_row["ACoS"])

        payloads.append(
            _build_period_payload(
                period_id=period_id,
                label=label,
                short_label=f"Week {week_index}",
                scorecard=scorecard_result.scorecard,
                negatives=cut_result.candidates,
                harvest=grow_result.candidates,
                metrics=metrics,
                config=config,
                estimated=estimated,
            )
        )
        current_start = current_end + pd.Timedelta(days=1)
        week_index += 1
    return payloads


def _slice_period_frame(
    frame: pd.DataFrame,
    row_start: pd.Series,
    row_end: pd.Series,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> tuple[pd.DataFrame, bool]:
    overlap_start = row_start.clip(lower=period_start)
    overlap_end = row_end.clip(upper=period_end)
    overlap_days = (overlap_end - overlap_start).dt.days + 1
    overlap_days = overlap_days.clip(lower=0)
    duration_days = ((row_end - row_start).dt.days + 1).clip(lower=1)
    weights = overlap_days / duration_days
    mask = weights > 0
    period_frame = frame.loc[mask].copy()
    if period_frame.empty:
        return period_frame, False

    period_weights = weights.loc[mask].to_numpy()
    for column in ["Clicks", "Impressions", "Spend", "Orders", "Sales"]:
        if column in period_frame:
            period_frame[column] = pd.to_numeric(period_frame[column], errors="coerce").fillna(0) * period_weights

    period_frame["Analysis Period Start"] = period_start
    period_frame["Analysis Period End"] = period_end
    period_frame["Analysis Period Id"] = f"{period_start:%Y-%m-%d}_{period_end:%Y-%m-%d}"
    period_frame["Analysis Period Label"] = _format_week_label(0, period_start, period_end).split(": ", 1)[-1]
    estimated = bool(((duration_days.loc[mask] > 7) | (period_weights < 1)).any())
    return period_frame, estimated


def _format_week_label(week_index: int, start: pd.Timestamp, end: pd.Timestamp) -> str:
    if start.year == end.year:
        date_label = f"{start:%b %-d} - {end:%b %-d, %Y}"
    else:
        date_label = f"{start:%b %-d, %Y} - {end:%b %-d, %Y}"
    if week_index:
        return f"Week {week_index}: {date_label}"
    return date_label


def _build_period_payload(
    *,
    period_id: str,
    label: str,
    short_label: str = "All",
    scorecard: pd.DataFrame,
    negatives: pd.DataFrame,
    harvest: pd.DataFrame,
    metrics: dict[str, Any],
    config: AnalysisConfig,
    estimated: bool = False,
) -> dict[str, Any]:
    cut_rows = negatives[negatives["Classification"].astype(str).str.startswith("NEGATIVE")].copy()
    review_rows = negatives[negatives["Classification"] == "REVIEW"].copy()
    grow_rows = harvest[harvest["Verdict"] == "HARVEST -> promote to Conv KW exact"].copy()

    brand = _scorecard_row(scorecard, "Brand Defense")
    discovery = _scorecard_row(scorecard, "Discovery")
    blended = _scorecard_row(scorecard, "Blended")

    brand_target_budget = brand["Sales"] * config.target_acos_brand
    discovery_target_budget = discovery["Sales"] * config.target_acos_discovery
    harvest_run_rate_spend = metrics["harvest_sales"] * metrics["harvest_weighted_acos"]

    return {
        "id": period_id,
        "label": label,
        "shortLabel": short_label,
        "estimated": estimated,
        "note": (
            "Estimated weekly split from a broader report range using day-overlap allocation."
            if estimated
            else "Actual source rows for this week."
        ),
        "metrics": metrics,
        "scorecard": [_json_safe(row) for row in scorecard.to_dict(orient="records")],
        "defaults": {
            "target_acos_pct": config.target_acos_blended * 100,
            "cut_adoption_pct": 80.0,
            "cpc_pressure_pct": 0.0,
            "cvr_lift_pct": 0.0,
            "brand_budget": round(brand_target_budget, 0),
            "discovery_budget": round(discovery_target_budget, 0),
            "harvest_budget": round(max(3500.0, harvest_run_rate_spend * 1.5), 0),
            "experiment_budget": 2500.0,
        },
        "benchmarks": {
            "brand_current_acos": brand["ACoS"],
            "discovery_current_acos": discovery["ACoS"],
            "blended_current_acos": blended["ACoS"],
            "harvest_current_acos": metrics["harvest_weighted_acos"],
            "experiment_default_acos": max(config.target_acos_blended * 1.25, discovery["ACoS"]),
            "brand_target_budget": brand_target_budget,
            "discovery_target_budget": discovery_target_budget,
            "current_spend": metrics["blended_spend"],
            "current_sales": metrics["blended_sales"],
            "harvest_run_rate_spend": harvest_run_rate_spend,
        },
        "tables": {
            "cut": _top_rows(cut_rows, ["Customer Search Term", "Spend", "Sales", "Orders", "ACoS", "Reason"], 12),
            "fix": _top_rows(review_rows, ["Customer Search Term", "Spend", "Sales", "Orders", "ACoS", "Reason"], 8),
            "grow": _top_rows(
                grow_rows,
                [
                    "Customer Search Term",
                    "Spend",
                    "Sales",
                    "Orders",
                    "ACoS",
                    "clicks_in_auto_disc",
                    "clicks_in_conv_exact",
                ],
                12,
            ),
        },
        "scenarios": _scenarios(config, brand_target_budget, discovery_target_budget, harvest_run_rate_spend),
    }


def _scenarios(
    config: AnalysisConfig,
    brand_target_budget: float,
    discovery_target_budget: float,
    harvest_run_rate_spend: float,
) -> dict[str, dict[str, Any]]:
    return {
        "efficiency": {
            "label": "Efficiency Reset",
            "description": (
                "Protect margin by ranking budget cuts on revenue loss per dollar removed, "
                "not by budget reduction alone."
            ),
            "cut_adoption_pct": 95.0,
            "cpc_pressure_pct": 0.0,
            "cvr_lift_pct": 0.0,
            "brand_budget": round(brand_target_budget, 0),
            "discovery_budget": round(discovery_target_budget * 0.92, 0),
            "harvest_budget": round(harvest_run_rate_spend * 1.1, 0),
            "experiment_budget": 1000.0,
        },
        "balanced": {
            "label": "Balanced Recovery",
            "description": "Restore ACoS discipline while reserving enough capital for exact-match harvest winners.",
            "cut_adoption_pct": 80.0,
            "cpc_pressure_pct": 2.0,
            "cvr_lift_pct": 1.0,
            "brand_budget": round(brand_target_budget, 0),
            "discovery_budget": round(discovery_target_budget, 0),
            "harvest_budget": round(max(4500.0, harvest_run_rate_spend * 1.7), 0),
            "experiment_budget": 2500.0,
        },
        "growth": {
            "label": "Growth Push",
            "description": "Accept measured spend expansion by shifting more budget into proven harvest demand.",
            "cut_adoption_pct": 70.0,
            "cpc_pressure_pct": 5.0,
            "cvr_lift_pct": 2.0,
            "brand_budget": round(brand_target_budget * 1.1, 0),
            "discovery_budget": round(discovery_target_budget * 1.05, 0),
            "harvest_budget": round(max(7500.0, harvest_run_rate_spend * 2.8), 0),
            "experiment_budget": 4000.0,
        },
    }


def write_dashboard(run_dir: str | Path, dashboard_dir: str | Path, template_dir: str | Path | None = None) -> dict[str, Path]:
    output = Path(dashboard_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = Path(template_dir).expanduser().resolve() if template_dir else _default_template_dir()
    for asset_name in DASHBOARD_ASSET_NAMES:
        source_path = source / asset_name
        if not source_path.exists():
            raise FileNotFoundError(f"Missing dashboard asset: {source_path}")
        target_path = output / asset_name
        if source_path.resolve() != target_path.resolve():
            shutil.copyfile(source_path, target_path)

    data = build_dashboard_data(run_dir)
    data_path = output / "data.js"
    data_path.write_text(
        "window.DASHBOARD_DATA = "
        + json.dumps(data, indent=2, sort_keys=True)
        + ";\n",
        encoding="utf-8",
    )
    return {
        "index": output / "index.html",
        "styles": output / "styles.css",
        "app": output / "app.js",
        "data": data_path,
    }


def write_dashboard_data(run_dir: str | Path, dashboard_dir: str | Path) -> Path:
    return write_dashboard(run_dir, dashboard_dir)["data"]


def _scorecard_row(scorecard: pd.DataFrame, bucket: str) -> dict[str, float]:
    row = scorecard[scorecard["Bucket"] == bucket]
    if row.empty:
        return {
            "Spend": 0.0,
            "Sales": 0.0,
            "Orders": 0.0,
            "Clicks": 0.0,
            "Impressions": 0.0,
            "ACoS": 0.0,
            "ROAS": 0.0,
            "CTR": 0.0,
            "CVR": 0.0,
            "Target ACoS": 0.0,
            "Variance": 0.0,
            "Dollar Over Target": 0.0,
        }
    record = row.iloc[0].to_dict()
    return {key: float(value) for key, value in record.items() if key != "Bucket"}


def _top_rows(frame: pd.DataFrame, columns: list[str], limit: int) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    sort_column = "Spend" if "Spend" in frame.columns else frame.columns[0]
    rows = frame.sort_values(sort_column, ascending=False).loc[:, columns].head(limit)
    return [_json_safe(row) for row in rows.to_dict(orient="records")]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Series):
        return _json_safe(value.to_dict())
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "Infinity"
        return value
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


def _default_template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "dashboard"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static dashboard data from analysis artifacts.")
    parser.add_argument("--run-dir", required=True, help="Directory containing run_summary.json and CSV artifacts.")
    parser.add_argument("--dashboard-dir", required=True, help="Dashboard directory where data.js should be written.")
    args = parser.parse_args()
    paths = write_dashboard(args.run_dir, args.dashboard_dir)
    print(paths["index"])


if __name__ == "__main__":
    main()
