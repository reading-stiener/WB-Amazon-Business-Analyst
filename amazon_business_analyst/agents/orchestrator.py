"""Run orchestrator for the Amazon search-term analysis agents."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amazon_business_analyst.agents.campaign_enrichment_agent import CampaignEnrichmentAgent
from amazon_business_analyst.agents.executive_dashboard_agent import ExecutiveDashboardAgent
from amazon_business_analyst.agents.harvest_grow_agent import HarvestGrowAgent
from amazon_business_analyst.agents.load_validation_agent import LoadValidationAgent
from amazon_business_analyst.agents.negative_kw_cut_agent import NegativeKeywordCutAgent
from amazon_business_analyst.agents.recommendation_writer_agent import RecommendationWriterAgent
from amazon_business_analyst.agents.regression_test_agent import RegressionTestAgent
from amazon_business_analyst.agents.scorecard_agent import ScorecardAgent
from amazon_business_analyst.agents.wandb_reliability_agent import ReliabilityRun
from amazon_business_analyst.config import AnalysisConfig
from amazon_business_analyst.io import ensure_output_dir


@dataclass(frozen=True)
class PipelineResult:
    output_dir: Path
    report_path: Path
    summary_path: Path
    metrics: dict[str, Any]
    dashboard_path: Path | None = None


class RunOrchestratorAgent:
    """Named agent wrapper for end-to-end pipeline execution."""

    def run(self, *args: Any, **kwargs: Any) -> PipelineResult:
        return run_pipeline(*args, **kwargs)


def run_pipeline(
    input_path: str,
    output_dir: str,
    *,
    sheet_name: str | None = None,
    config: AnalysisConfig | None = None,
    enable_wandb: bool = False,
    wandb_project: str | None = None,
    wandb_run_name: str | None = None,
    regression_baseline: str | None = None,
) -> PipelineResult:
    config = config or AnalysisConfig()
    out_dir = ensure_output_dir(output_dir)
    reliability = ReliabilityRun(
        output_dir=out_dir,
        config=config,
        enable_wandb=enable_wandb,
        project=wandb_project,
        run_name=wandb_run_name,
    )

    try:
        load_result = LoadValidationAgent().run(input_path, sheet_name=sheet_name)
        raw_path = out_dir / "validated_raw_search_terms.csv"
        load_result.table.to_csv(raw_path, index=False)
        reliability.log_metrics(load_result.report)
        reliability.log_table_artifact("validated_raw_search_terms", load_result.table, raw_path)

        enrich_result = CampaignEnrichmentAgent().run(load_result.table)
        enriched_path = out_dir / "enriched_search_terms.csv"
        enrich_result.table.to_csv(enriched_path, index=False)
        reliability.log_metrics(
            {
                "other_campaign_count": enrich_result.report["other_campaign_count"],
            }
        )
        reliability.log_table_artifact("enriched_search_terms", enrich_result.table, enriched_path)

        scorecard_result = ScorecardAgent().run(enrich_result.table, config)
        scorecard_path = out_dir / "scorecard.csv"
        scorecard_result.scorecard.to_csv(scorecard_path, index=False)
        reliability.log_metrics(scorecard_result.metrics)
        reliability.log_self_checks({f"scorecard_{key}": value for key, value in scorecard_result.self_checks.items()})
        reliability.log_table_artifact("scorecard", scorecard_result.scorecard, scorecard_path)

        cut_result = NegativeKeywordCutAgent().run(enrich_result.table, config)
        cut_path = out_dir / "negative_keyword_candidates.csv"
        cut_summary_path = out_dir / "negative_keyword_summary.csv"
        cut_result.candidates.to_csv(cut_path, index=False)
        cut_result.summary.to_csv(cut_summary_path, index=False)
        reliability.log_metrics(cut_result.metrics)
        reliability.log_table_artifact("negative_keyword_candidates", cut_result.candidates, cut_path)
        reliability.log_table_artifact("negative_keyword_summary", cut_result.summary, cut_summary_path)

        grow_result = HarvestGrowAgent().run(enrich_result.table, config)
        harvest_path = out_dir / "harvest_candidates.csv"
        grow_result.candidates.to_csv(harvest_path, index=False)
        reliability.log_metrics(grow_result.summary)
        reliability.log_self_checks({f"harvest_{key}": value for key, value in grow_result.self_checks.items()})
        reliability.log_table_artifact("harvest_candidates", grow_result.candidates, harvest_path)

        writer_result = RecommendationWriterAgent().run(
            out_dir,
            config,
            scorecard_result.scorecard,
            scorecard_result.narrative,
            cut_result.candidates,
            grow_result.candidates,
        )
        reliability.log_file_artifact("next_month_recommendations", writer_result.report_path, "report")

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

        regression_result = RegressionTestAgent().run(metrics, regression_baseline)
        regression_path = out_dir / "regression_test_report.json"
        regression_path.write_text(json.dumps(regression_result.report, indent=2, sort_keys=True), encoding="utf-8")
        reliability.log_file_artifact("regression_test_report", regression_path, "validation")
        reliability.log_metrics({"regression_passed": int(regression_result.passed)})
        if not regression_result.passed:
            raise AssertionError(f"Regression test failed: {regression_result.report}")

        summary = {
            "input_path": str(Path(input_path).expanduser()),
            "output_dir": str(out_dir),
            "report_path": str(writer_result.report_path),
            "config": config.to_dict(),
            "metrics": metrics,
            "self_checks": {
                **scorecard_result.self_checks,
                **grow_result.self_checks,
            },
            "artifacts": {
                "validated_raw": str(raw_path),
                "enriched": str(enriched_path),
                "scorecard": str(scorecard_path),
                "negative_keyword_candidates": str(cut_path),
                "negative_keyword_summary": str(cut_summary_path),
                "harvest_candidates": str(harvest_path),
                "recommendations": str(writer_result.report_path),
                "regression_report": str(regression_path),
            },
        }
        summary_path = out_dir / "run_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

        dashboard_result = ExecutiveDashboardAgent().run(out_dir)
        summary["dashboard_path"] = str(dashboard_result.index_path)
        summary["artifacts"].update(
            {
                "dashboard_index": str(dashboard_result.index_path),
                "dashboard_data": str(dashboard_result.data_path),
                "dashboard_styles": str(dashboard_result.asset_paths["styles"]),
                "dashboard_app": str(dashboard_result.asset_paths["app"]),
            }
        )
        for name, path in dashboard_result.asset_paths.items():
            reliability.log_file_artifact(f"dashboard_{name}", path, "dashboard")
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

        reliability.log_file_artifact("run_summary", summary_path, "summary")
        manifest_path = reliability.finish("success")
        summary["artifacts"]["wandb_local_manifest"] = str(manifest_path)
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        return PipelineResult(out_dir, writer_result.report_path, summary_path, metrics, dashboard_result.index_path)
    except Exception:
        reliability.finish("failed")
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Amazon Sponsored Products search-term analysis agents.")
    parser.add_argument("--input", required=True, help="Path to monthly Amazon search-term CSV/XLSX.")
    parser.add_argument("--sheet", default=None, help="Excel sheet name. Defaults to Data when present.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts.")
    parser.add_argument("--enable-wandb", action="store_true", help="Log to W&B if wandb is installed.")
    parser.add_argument("--wandb-project", default="amazon-business-analyst", help="W&B project name.")
    parser.add_argument("--wandb-run-name", default=None, help="Optional W&B run name.")
    parser.add_argument("--regression-baseline", default=None, help="Optional JSON baseline for regression validation.")
    parser.add_argument("--target-acos-blended", type=float, default=None)
    parser.add_argument("--target-acos-discovery", type=float, default=None)
    parser.add_argument("--target-acos-brand", type=float, default=None)
    parser.add_argument("--neg-zero-order-min-spend", type=float, default=None)
    parser.add_argument("--neg-high-acos-min-spend", type=float, default=None)
    parser.add_argument("--high-acos-cutoff", type=float, default=None)
    parser.add_argument("--review-band-min", type=float, default=None)
    parser.add_argument("--review-band-max", type=float, default=None)
    parser.add_argument("--harvest-min-orders", type=int, default=None)
    parser.add_argument("--harvest-max-acos", type=float, default=None)
    parser.add_argument("--report-max-rows", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AnalysisConfig.from_mapping(
        {
            "target_acos_blended": args.target_acos_blended,
            "target_acos_discovery": args.target_acos_discovery,
            "target_acos_brand": args.target_acos_brand,
            "neg_zero_order_min_spend": args.neg_zero_order_min_spend,
            "neg_high_acos_min_spend": args.neg_high_acos_min_spend,
            "high_acos_cutoff": args.high_acos_cutoff,
            "review_band_min": args.review_band_min,
            "review_band_max": args.review_band_max,
            "harvest_min_orders": args.harvest_min_orders,
            "harvest_max_acos": args.harvest_max_acos,
            "report_max_rows": args.report_max_rows,
        }
    )
    result = run_pipeline(
        args.input,
        args.output_dir,
        sheet_name=args.sheet,
        config=config,
        enable_wandb=args.enable_wandb,
        wandb_project=args.wandb_project,
        wandb_run_name=args.wandb_run_name,
        regression_baseline=args.regression_baseline,
    )
    print(
        json.dumps(
            {
                "report_path": str(result.report_path),
                "dashboard_path": str(result.dashboard_path),
                "summary_path": str(result.summary_path),
                "metrics": result.metrics,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
