from lunar_planner.demo import generate_scene
from lunar_planner.landing import rank_landing_sites


def test_landing_sites_respect_constraints():
    scene = generate_scene()
    sites = rank_landing_sites(scene, limit=8)
    assert len(sites) == 8
    assert all(site.slope_deg <= 14 for site in sites)
    assert all(site.roughness <= 0.58 for site in sites)
    assert all(site.illumination >= 0.16 for site in sites)


def test_landing_sites_are_ranked_and_spaced():
    scene = generate_scene()
    sites = rank_landing_sites(scene, limit=6)
    assert [site.score for site in sites] == sorted((site.score for site in sites), reverse=True)
    for index, site in enumerate(sites):
        for other in sites[index + 1 :]:
            distance = ((site.point.row - other.point.row) ** 2 + (site.point.col - other.point.col) ** 2) ** 0.5
            assert distance >= 5
