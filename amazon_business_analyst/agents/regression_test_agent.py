"""Regression test agent for hand-verified monthly baselines."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RegressionTestResult:
    passed: bool
    report: dict[str, Any]


class RegressionTestAgent:
    """Compare headline metrics with a hand-verified baseline."""

    DEFAULT_ABS_TOLERANCE = 0.01

    def run(self, actual_metrics: dict[str, Any], baseline_path: str | None) -> RegressionTestResult:
        if not baseline_path:
            return RegressionTestResult(passed=True, report={"status": "skipped", "reason": "No baseline path provided"})

        baseline = json.loads(Path(baseline_path).expanduser().read_text(encoding="utf-8"))
        expected = baseline.get("expected_metrics", baseline)
        tolerance = float(baseline.get("abs_tolerance", self.DEFAULT_ABS_TOLERANCE))

        diffs = []
        for key, expected_value in expected.items():
            actual_value = actual_metrics.get(key)
            if isinstance(expected_value, (int, float)):
                if actual_value is None or not math.isclose(float(actual_value), float(expected_value), abs_tol=tolerance):
                    diffs.append({"metric": key, "expected": expected_value, "actual": actual_value})
            elif actual_value != expected_value:
                diffs.append({"metric": key, "expected": expected_value, "actual": actual_value})

        passed = not diffs
        return RegressionTestResult(
            passed=passed,
            report={"status": "passed" if passed else "failed", "baseline": str(Path(baseline_path).expanduser()), "diffs": diffs},
        )
