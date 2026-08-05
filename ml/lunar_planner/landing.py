from __future__ import annotations

import math

import numpy as np

from .analysis import characterize_ice
from .types import GridPoint, LandingSite, LunarScene

CELL_METERS = 30.0


def _nearest_ice_distance(row: int, col: int, mask: np.ndarray) -> float:
    points = np.argwhere(mask)
    if not len(points):
        return float("inf")
    distances = np.sqrt((points[:, 0] - row) ** 2 + (points[:, 1] - col) ** 2)
    return float(distances.min() * CELL_METERS)


def rank_landing_sites(scene: LunarScene, limit: int = 8, min_spacing_cells: int = 5) -> list[LandingSite]:
    ice = characterize_ice(scene)
    target_mask = (ice.probability >= 0.72) & (ice.confidence >= 0.58)
    candidates: list[LandingSite] = []

    for row in range(2, scene.size - 2):
        for col in range(2, scene.size - 2):
            slope = float(scene.slope_deg[row, col])
            roughness = float(scene.roughness[row, col])
            illumination = float(scene.illumination[row, col])
            communication = float(scene.communication[row, col])
            if slope > 14.0 or roughness > 0.58 or illumination < 0.16 or communication < 0.28:
                continue
            distance = _nearest_ice_distance(row, col, target_mask)
            safety = np.clip(1 - slope / 16.0, 0, 1) * 0.55 + np.clip(1 - roughness, 0, 1) * 0.45
            proximity = math.exp(-distance / 650.0) if math.isfinite(distance) else 0.0
            local_ice = float(ice.probability[row, col])
            science = 0.72 * proximity + 0.28 * local_ice
            operations = 0.56 * illumination + 0.44 * communication
            score = 100 * (0.48 * safety + 0.31 * operations + 0.21 * science)
            candidates.append(
                LandingSite(
                    id=f"LS-{row:02d}{col:02d}",
                    point=GridPoint(row, col),
                    score=round(float(score), 2),
                    slope_deg=round(slope, 2),
                    roughness=round(roughness, 3),
                    illumination=round(illumination, 3),
                    communication=round(communication, 3),
                    nearest_ice_distance_m=round(distance, 1),
                    ice_probability=round(local_ice, 3),
                    safety_score=round(float(safety * 100), 2),
                    science_score=round(float(science * 100), 2),
                )
            )

    candidates.sort(key=lambda item: item.score, reverse=True)
    selected: list[LandingSite] = []
    for candidate in candidates:
        if all(
            math.hypot(
                candidate.point.row - existing.point.row,
                candidate.point.col - existing.point.col,
            )
            >= min_spacing_cells
            for existing in selected
        ):
            selected.append(candidate)
        if len(selected) >= limit:
            break
    return selected
