"""Executive dashboard agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from amazon_business_analyst.dashboard_generator import write_dashboard


@dataclass(frozen=True)
class ExecutiveDashboardResult:
    dashboard_dir: Path
    index_path: Path
    data_path: Path
    asset_paths: dict[str, Path]


class ExecutiveDashboardAgent:
    """Generate web dashboard assets for weekly business-leader review."""

    def run(self, run_dir: str | Path, dashboard_dir: str | Path | None = None) -> ExecutiveDashboardResult:
        source = Path(run_dir).expanduser().resolve()
        target = Path(dashboard_dir).expanduser().resolve() if dashboard_dir else source / "dashboard"
        asset_paths = write_dashboard(source, target)
        return ExecutiveDashboardResult(
            dashboard_dir=target,
            index_path=asset_paths["index"],
            data_path=asset_paths["data"],
            asset_paths=asset_paths,
        )
