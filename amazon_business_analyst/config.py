"""Configuration for the search-term analysis pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class AnalysisConfig:
    target_acos_blended: float = 0.25
    target_acos_discovery: float = 0.25
    target_acos_brand: float = 0.20
    neg_zero_order_min_spend: float = 50.0
    neg_high_acos_min_spend: float = 100.0
    high_acos_cutoff: float = 1.0
    review_band_min: float = 0.5
    review_band_max: float = 1.0
    harvest_min_orders: int = 3
    harvest_max_acos: float = 0.20
    report_max_rows: int = 50

    @classmethod
    def from_mapping(cls, overrides: Mapping[str, Any] | None = None) -> "AnalysisConfig":
        if not overrides:
            return cls()
        allowed = set(cls.__dataclass_fields__)
        unknown = sorted(set(overrides) - allowed)
        if unknown:
            raise ValueError(f"Unknown config key(s): {', '.join(unknown)}")
        return cls(**{key: value for key, value in overrides.items() if value is not None})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
