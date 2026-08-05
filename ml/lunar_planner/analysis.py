from __future__ import annotations

import numpy as np

from .types import IceAssessment, LunarScene


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def characterize_ice(scene: LunarScene) -> IceAssessment:
    """Fuse dual-frequency radar, polarization, thermal and optical evidence.

    High L-band CPR with low DOP is treated as stronger volumetric-scattering
    evidence, while roughness-only CPR enhancement is explicitly penalized.
    """
    cpr_evidence = (scene.cpr_l - 0.95) / 0.18
    low_dop = (0.16 - scene.dop) / 0.045
    depth_contrast = (scene.cpr_l - scene.cpr_s - 0.08) / 0.10
    cold_trap = (78.0 - scene.temperature_k) / 16.0
    hydration = (scene.hydration_index - 0.38) / 0.14
    psr_bonus = scene.psr_mask.astype(float) * 1.05

    roughness_false_positive = np.clip(
        0.62 * scene.roughness + 0.38 * (1 - scene.radar_coherence), 0, 1
    )
    evidence = (
        0.88 * cpr_evidence
        + 0.92 * low_dop
        + 0.62 * depth_contrast
        + 0.55 * cold_trap
        + 0.38 * hydration
        + psr_bonus
        - 1.25 * roughness_false_positive
    )
    probability = _sigmoid(evidence)

    agreement = (
        (scene.cpr_l > 1.0).astype(float)
        + (scene.dop < 0.16).astype(float)
        + (scene.temperature_k < 85).astype(float)
        + scene.psr_mask.astype(float)
        + (scene.hydration_index > 0.42).astype(float)
    ) / 5.0
    confidence = np.clip(0.34 + 0.58 * agreement - 0.22 * roughness_false_positive, 0.05, 0.98)
    return IceAssessment(
        probability=probability.astype(np.float32),
        confidence=confidence.astype(np.float32),
        roughness_false_positive_risk=roughness_false_positive.astype(np.float32),
        evidence_score=evidence.astype(np.float32),
    )


def assess_scene(scene: LunarScene) -> dict[str, float | int]:
    assessment = characterize_ice(scene)
    high_confidence = (assessment.probability >= 0.72) & (assessment.confidence >= 0.62)
    return {
        "grid_size": scene.size,
        "cell_resolution_m": 30,
        "area_km2": round((scene.size * 30) ** 2 / 1_000_000, 3),
        "psr_fraction": round(float(scene.psr_mask.mean()), 4),
        "high_probability_cells": int((assessment.probability >= 0.72).sum()),
        "high_confidence_ice_cells": int(high_confidence.sum()),
        "mean_ice_probability": round(float(assessment.probability.mean()), 4),
        "max_ice_probability": round(float(assessment.probability.max()), 4),
        "mean_slope_deg": round(float(scene.slope_deg.mean()), 3),
        "safe_terrain_fraction": round(float(((scene.slope_deg < 12) & (scene.roughness < 0.5)).mean()), 4),
    }
