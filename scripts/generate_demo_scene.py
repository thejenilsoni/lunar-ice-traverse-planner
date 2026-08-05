from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))

from lunar_planner.demo import generate_scene
from lunar_planner.landing import rank_landing_sites
from lunar_planner.routing import plan_traverse
from lunar_planner.serialization import scene_payload


def main() -> None:
    scene = generate_scene()
    sites = rank_landing_sites(scene)
    plan = plan_traverse(scene, sites[0].point)
    payload = scene_payload(scene)
    payload["landing_sites"] = [site.as_dict() for site in sites]
    payload["recommended_traverse"] = plan.as_dict()
    output = Path("data/generated/lunar_south_pole_demo.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
