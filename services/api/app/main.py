from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from lunar_planner.analysis import characterize_ice
from lunar_planner.demo import generate_scene
from lunar_planner.landing import rank_landing_sites
from lunar_planner.routing import plan_traverse
from lunar_planner.serialization import scene_payload
from lunar_planner.types import GridPoint

from .schemas import IceQuery, LandingRequest, TraverseRequest

app = FastAPI(
    title="LunaTraverse API",
    version="0.1.0",
    description="Lunar south-polar ice characterization, landing-site ranking and rover traverse planning.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "luna-traverse"}


@app.get("/v1/scene")
def get_scene(seed: int = 2026, size: int = 48):
    if not 24 <= size <= 96:
        raise HTTPException(status_code=422, detail="size must be between 24 and 96")
    return scene_payload(generate_scene(seed=seed, size=size))


@app.post("/v1/ice/query")
def query_ice(request: IceQuery):
    scene = generate_scene(seed=request.seed)
    if request.row >= scene.size or request.col >= scene.size:
        raise HTTPException(status_code=422, detail="point is outside the scene")
    ice = characterize_ice(scene)
    row, col = request.row, request.col
    return {
        "point": {"row": row, "col": col},
        "ice_probability": round(float(ice.probability[row, col]), 4),
        "confidence": round(float(ice.confidence[row, col]), 4),
        "cpr_l": round(float(scene.cpr_l[row, col]), 4),
        "cpr_s": round(float(scene.cpr_s[row, col]), 4),
        "dop": round(float(scene.dop[row, col]), 4),
        "temperature_k": round(float(scene.temperature_k[row, col]), 2),
        "psr": bool(scene.psr_mask[row, col]),
        "roughness_false_positive_risk": round(float(ice.roughness_false_positive_risk[row, col]), 4),
    }


@app.post("/v1/landing-sites/rank")
def landing_sites(request: LandingRequest):
    scene = generate_scene(seed=request.seed)
    sites = rank_landing_sites(scene, limit=request.limit)
    return {"seed": request.seed, "sites": [site.as_dict() for site in sites]}


@app.post("/v1/traverses/plan")
def traverse(request: TraverseRequest):
    scene = generate_scene(seed=request.seed)
    points = [request.origin, request.target] if request.target else [request.origin]
    if any(point and (point.row >= scene.size or point.col >= scene.size) for point in points):
        raise HTTPException(status_code=422, detail="origin or target is outside the scene")
    origin = GridPoint(request.origin.row, request.origin.col)
    target = GridPoint(request.target.row, request.target.col) if request.target else None
    plan = plan_traverse(
        scene,
        origin=origin,
        target=target,
        battery_wh=request.battery_wh,
        speed_m_per_hour=request.speed_m_per_hour,
        risk_tolerance=request.risk_tolerance,
    )
    return plan.as_dict()
