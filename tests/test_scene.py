import numpy as np

from lunar_planner.analysis import assess_scene, characterize_ice
from lunar_planner.demo import generate_scene


def test_scene_is_deterministic():
    first = generate_scene(seed=2026)
    second = generate_scene(seed=2026)
    np.testing.assert_allclose(first.elevation_m, second.elevation_m)
    np.testing.assert_allclose(first.cpr_l, second.cpr_l)


def test_scene_has_shadow_and_safe_terrain():
    scene = generate_scene()
    summary = assess_scene(scene)
    assert summary["psr_fraction"] > 0.02
    assert summary["safe_terrain_fraction"] > 0.1
    assert scene.slope_deg.shape == (48, 48)


def test_ice_fusion_detects_high_probability_cells():
    scene = generate_scene()
    assessment = characterize_ice(scene)
    assert float(assessment.probability.max()) > 0.85
    assert int((assessment.probability > 0.72).sum()) > 5
    assert np.all((assessment.confidence >= 0) & (assessment.confidence <= 1))


def test_roughness_false_positive_is_explicit():
    scene = generate_scene()
    assessment = characterize_ice(scene)
    rough = np.unravel_index(np.argmax(scene.roughness), scene.roughness.shape)
    assert assessment.roughness_false_positive_risk[rough] > 0.45
