"""W&B reliability agent with a local fallback manifest."""

from __future__ import annotations

import importlib.util
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from amazon_business_analyst.config import AnalysisConfig


@dataclass
class ReliabilityRun:
    output_dir: Path
    config: AnalysisConfig
    enable_wandb: bool = False
    project: str | None = None
    run_name: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    self_checks: dict[str, bool] = field(default_factory=dict)
    _wandb: Any = None
    _wandb_run: Any = None

    def __post_init__(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.enable_wandb and importlib.util.find_spec("wandb"):
            import wandb  # type: ignore

            self._wandb = wandb
            self._wandb_run = wandb.init(project=self.project, name=self.run_name, config=self.config.to_dict())

    def log_metrics(self, metrics: dict[str, Any]) -> None:
        clean_metrics = {key: self._json_safe(value) for key, value in metrics.items()}
        self.metrics.update(clean_metrics)
        if self._wandb_run is not None:
            scalar_metrics = {
                key: value
                for key, value in clean_metrics.items()
                if isinstance(value, (str, bool, int, float)) or value is None
            }
            self._wandb.log(scalar_metrics)

    def log_self_checks(self, checks: dict[str, bool]) -> None:
        self.self_checks.update(checks)
        self.log_metrics({f"self_check/{key}": int(value) for key, value in checks.items()})

    def log_table_artifact(self, name: str, table: pd.DataFrame, path: Path) -> None:
        artifact = {"name": name, "type": "table", "path": str(path), "rows": int(len(table)), "columns": list(table.columns)}
        self.artifacts.append(artifact)
        if self._wandb_run is not None:
            wandb_artifact = self._wandb.Artifact(name=name, type="dataset")
            wandb_artifact.add_file(str(path))
            self._wandb_run.log_artifact(wandb_artifact)

    def log_file_artifact(self, name: str, path: Path, artifact_type: str) -> None:
        artifact = {"name": name, "type": artifact_type, "path": str(path)}
        self.artifacts.append(artifact)
        if self._wandb_run is not None:
            wandb_artifact = self._wandb.Artifact(name=name, type=artifact_type)
            wandb_artifact.add_file(str(path))
            self._wandb_run.log_artifact(wandb_artifact)

    def finish(self, status: str = "success") -> Path:
        manifest = {
            "status": status,
            "wandb_enabled": self._wandb_run is not None,
            "config": self.config.to_dict(),
            "metrics": self.metrics,
            "self_checks": self.self_checks,
            "artifacts": self.artifacts,
        }
        manifest_path = self.output_dir / "wandb_local_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        if self._wandb_run is not None:
            self._wandb_run.finish(exit_code=0 if status == "success" else 1)
        return manifest_path

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, (str, bool, int)) or value is None:
            return value
        if isinstance(value, float):
            if math.isinf(value):
                return "Infinity"
            if math.isnan(value):
                return None
            return value
        return value


class WandbReliabilityAgent(ReliabilityRun):
    """Named agent wrapper for the reliability/logging role."""
