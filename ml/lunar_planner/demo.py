from __future__ import annotations

import numpy as np

from .types import LunarScene


def _crater(y: np.ndarray, x: np.ndarray, cy: float, cx: float, radius: float, depth: float) -> np.ndarray:
    distance = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
    bowl = -depth * np.clip(1 - (distance / radius) ** 2, 0, 1) ** 1.7
    rim = depth * 0.18 * np.exp(-((distance - radius) ** 2) / max(1.4, radius * 0.14) ** 2)
    return bowl + rim


def _normalise(values: np.ndarray) -> np.ndarray:
    low = float(values.min())
    span = float(values.max() - low)
    return np.zeros_like(values) if span < 1e-9 else (values - low) / span


def generate_scene(seed: int = 2026, size: int = 48) -> LunarScene:
    """Generate a deterministic lunar south-polar analogue for software validation.

    The scene deliberately contains rough-rock radar confounders as well as buried-ice
    deposits so that the fusion model must use polarimetry, shadow and terrain jointly.
    """
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size]

    elevation = 160 + 1.8 * x + 0.8 * y
    craters = [
        (13.0, 14.5, 8.5, 185.0),
        (31.0, 34.0, 10.0, 240.0),
        (36.0, 13.0, 6.8, 150.0),
        (17.0, 37.0, 5.5, 112.0),
    ]
    for cy, cx, radius, depth in craters:
        elevation += _crater(y, x, cy, cx, radius, depth)
    elevation += rng.normal(0, 3.6, size=(size, size))

    gy, gx = np.gradient(elevation, 30.0)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    laplacian = np.abs(
        -4 * elevation
        + np.roll(elevation, 1, 0)
        + np.roll(elevation, -1, 0)
        + np.roll(elevation, 1, 1)
        + np.roll(elevation, -1, 1)
    )
    roughness = np.clip(_normalise(laplacian) * 0.85 + rng.normal(0.04, 0.025, (size, size)), 0, 1)

    sun_azimuth = np.deg2rad(68.0)
    incidence = np.clip(0.18 + 0.9 * (gx * np.cos(sun_azimuth) + gy * np.sin(sun_azimuth)), -1, 1)
    crater_depth = _normalise(elevation.max() - elevation)
    illumination = np.clip(0.42 + 0.35 * incidence - 0.58 * crater_depth, 0, 1)
    illumination = np.clip(illumination + rng.normal(0, 0.025, (size, size)), 0, 1)
    psr = illumination < 0.12
    temperature = np.clip(32 + 92 * illumination + 18 * (1 - crater_depth), 24, 145)

    true_ice = np.zeros((size, size), dtype=float)
    deposits = [
        (14.0, 14.0, 4.4, 0.88),
        (32.5, 34.0, 5.3, 0.95),
        (36.0, 12.0, 3.0, 0.72),
    ]
    for cy, cx, sigma, strength in deposits:
        true_ice += strength * np.exp(-(((y - cy) ** 2 + (x - cx) ** 2) / (2 * sigma**2)))
    true_ice *= np.clip((0.22 - illumination) / 0.22, 0, 1)
    true_ice = np.clip(true_ice, 0, 1)

    rock_confounder = np.clip((roughness - 0.42) * 1.9, 0, 0.75)
    cpr_l = np.clip(0.58 + 0.88 * true_ice + 0.52 * rock_confounder + rng.normal(0, 0.055, (size, size)), 0.15, 2.2)
    cpr_s = np.clip(0.56 + 0.55 * true_ice + 0.58 * rock_confounder + rng.normal(0, 0.055, (size, size)), 0.12, 2.1)
    dop = np.clip(0.34 - 0.27 * true_ice + 0.08 * rock_confounder + rng.normal(0, 0.018, (size, size)), 0.03, 0.58)
    coherence = np.clip(0.84 - 0.34 * roughness - 0.21 * true_ice + rng.normal(0, 0.025, (size, size)), 0.15, 0.98)
    hydration = np.clip(0.18 + 0.48 * true_ice + 0.15 * (1 - illumination) + rng.normal(0, 0.035, (size, size)), 0, 1)

    ridge = _normalise(elevation)
    communication = np.clip(0.28 + 0.62 * ridge - 0.15 * np.clip(slope / 25, 0, 1), 0, 1)

    return LunarScene(
        seed=seed,
        size=size,
        elevation_m=elevation.astype(np.float32),
        slope_deg=slope.astype(np.float32),
        roughness=roughness.astype(np.float32),
        illumination=illumination.astype(np.float32),
        psr_mask=psr,
        temperature_k=temperature.astype(np.float32),
        cpr_l=cpr_l.astype(np.float32),
        cpr_s=cpr_s.astype(np.float32),
        dop=dop.astype(np.float32),
        radar_coherence=coherence.astype(np.float32),
        hydration_index=hydration.astype(np.float32),
        communication=communication.astype(np.float32),
        true_ice_fraction=true_ice.astype(np.float32),
    )
