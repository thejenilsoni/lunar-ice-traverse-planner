from __future__ import annotations

from typing import Any

import numpy as np

from .analysis import assess_scene, characterize_ice
from .types import LunarScene


def _round_grid(values: np.ndarray, digits: int = 3) -> list[list[float]]:
    return np.round(values.astype(float), digits).tolist()


def scene_payload(scene: LunarScene) -> dict[str, Any]:
    ice = characterize_ice(scene)
    return {
        "seed": scene.seed,
        "size": scene.size,
        "cell_resolution_m": 30,
        "summary": assess_scene(scene),
        "layers": {
            "elevation_m": _round_grid(scene.elevation_m, 1),
            "slope_deg": _round_grid(scene.slope_deg, 2),
            "roughness": _round_grid(scene.roughness),
            "illumination": _round_grid(scene.illumination),
            "psr": scene.psr_mask.astype(int).tolist(),
            "temperature_k": _round_grid(scene.temperature_k, 1),
            "cpr_l": _round_grid(scene.cpr_l),
            "cpr_s": _round_grid(scene.cpr_s),
            "dop": _round_grid(scene.dop),
            "hydration": _round_grid(scene.hydration_index),
            "communication": _round_grid(scene.communication),
            "ice_probability": _round_grid(ice.probability),
            "ice_confidence": _round_grid(ice.confidence),
            "roughness_false_positive_risk": _round_grid(ice.roughness_false_positive_risk),
        },
    }
