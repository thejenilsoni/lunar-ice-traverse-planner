from lunar_planner.demo import generate_scene
from lunar_planner.landing import rank_landing_sites
from lunar_planner.routing import plan_traverse, select_science_target


def test_science_target_is_inside_scene():
    scene = generate_scene()
    origin = rank_landing_sites(scene, limit=1)[0].point
    target = select_science_target(scene, origin)
    assert 0 <= target.row < scene.size
    assert 0 <= target.col < scene.size


def test_traverse_returns_energy_and_path():
    scene = generate_scene()
    origin = rank_landing_sites(scene, limit=1)[0].point
    plan = plan_traverse(scene, origin, battery_wh=6000)
    assert len(plan.path) > 1
    assert plan.distance_m > 0
    assert plan.estimated_energy_wh > 0
    assert plan.feasible
    assert plan.energy_margin_wh > 0


def test_low_battery_can_mark_plan_infeasible():
    scene = generate_scene()
    origin = rank_landing_sites(scene, limit=1)[0].point
    plan = plan_traverse(scene, origin, battery_wh=120)
    assert not plan.feasible
    assert plan.energy_margin_wh < 0
