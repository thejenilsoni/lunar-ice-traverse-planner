from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class GridPoint:
    row: int
    col: int

    def as_dict(self) -> dict[str, int]:
        return {"row": self.row, "col": self.col}


@dataclass
class LunarScene:
    seed: int
    size: int
    elevation_m: np.ndarray
    slope_deg: np.ndarray
    roughness: np.ndarray
    illumination: np.ndarray
    psr_mask: np.ndarray
    temperature_k: np.ndarray
    cpr_l: np.ndarray
    cpr_s: np.ndarray
    dop: np.ndarray
    radar_coherence: np.ndarray
    hydration_index: np.ndarray
    communication: np.ndarray
    true_ice_fraction: np.ndarray


@dataclass(frozen=True)
class IceAssessment:
    probability: np.ndarray
    confidence: np.ndarray
    roughness_false_positive_risk: np.ndarray
    evidence_score: np.ndarray


@dataclass(frozen=True)
class LandingSite:
    id: str
    point: GridPoint
    score: float
    slope_deg: float
    roughness: float
    illumination: float
    communication: float
    nearest_ice_distance_m: float
    ice_probability: float
    safety_score: float
    science_score: float

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["point"] = self.point.as_dict()
        return data


@dataclass(frozen=True)
class TraversePlan:
    origin: GridPoint
    target: GridPoint
    path: list[GridPoint]
    distance_m: float
    estimated_energy_wh: float
    duration_hours: float
    mean_slope_deg: float
    max_slope_deg: float
    shadow_fraction: float
    hazard_score: float
    science_value: float
    feasible: bool
    energy_margin_wh: float
    rationale: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "origin": self.origin.as_dict(),
            "target": self.target.as_dict(),
            "path": [point.as_dict() for point in self.path],
            "distance_m": self.distance_m,
            "estimated_energy_wh": self.estimated_energy_wh,
            "duration_hours": self.duration_hours,
            "mean_slope_deg": self.mean_slope_deg,
            "max_slope_deg": self.max_slope_deg,
            "shadow_fraction": self.shadow_fraction,
            "hazard_score": self.hazard_score,
            "science_value": self.science_value,
            "feasible": self.feasible,
            "energy_margin_wh": self.energy_margin_wh,
            "rationale": self.rationale,
        }
