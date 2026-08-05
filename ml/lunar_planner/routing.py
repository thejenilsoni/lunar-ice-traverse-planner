from __future__ import annotations

import heapq
import math
from collections import defaultdict

import numpy as np

from .analysis import characterize_ice
from .types import GridPoint, LunarScene, TraversePlan

CELL_METERS = 30.0


def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _neighbours(row: int, col: int, size: int):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size:
            yield nr, nc, math.sqrt(2) if dr and dc else 1.0


def _reachable_mask(scene: LunarScene, origin: GridPoint) -> np.ndarray:
    mask = np.zeros((scene.size, scene.size), dtype=bool)
    queue: list[tuple[int, int]] = [(origin.row, origin.col)]
    mask[origin.row, origin.col] = True
    while queue:
        row, col = queue.pop()
        for nr, nc, _ in _neighbours(row, col, scene.size):
            if mask[nr, nc]:
                continue
            if scene.slope_deg[nr, nc] > 25.0 or scene.roughness[nr, nc] > 0.88:
                continue
            mask[nr, nc] = True
            queue.append((nr, nc))
    return mask


def select_science_target(scene: LunarScene, origin: GridPoint) -> GridPoint:
    ice = characterize_ice(scene)
    y, x = np.mgrid[0 : scene.size, 0 : scene.size]
    distance = np.hypot(y - origin.row, x - origin.col)
    reachable_bonus = np.exp(-distance / 18.0)
    terrain_penalty = np.clip(scene.slope_deg / 24.0, 0, 1) + 0.7 * scene.roughness
    utility = 0.72 * ice.probability + 0.30 * ice.confidence + 0.15 * reachable_bonus - 0.26 * terrain_penalty
    reachable = _reachable_mask(scene, origin)
    utility[~reachable] = -1
    utility[scene.slope_deg > 22] = -1
    utility[distance < 4.0] = -1
    target = np.unravel_index(int(np.argmax(utility)), utility.shape)
    return GridPoint(int(target[0]), int(target[1]))


def plan_traverse(
    scene: LunarScene,
    origin: GridPoint,
    target: GridPoint | None = None,
    battery_wh: float = 2200.0,
    speed_m_per_hour: float = 90.0,
    risk_tolerance: float = 0.45,
) -> TraversePlan:
    target = target or select_science_target(scene, origin)
    ice = characterize_ice(scene)
    start = (origin.row, origin.col)
    goal = (target.row, target.col)
    frontier: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    cost_so_far = defaultdict(lambda: float("inf"))
    cost_so_far[start] = 0.0

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for nr, nc, step in _neighbours(*current, scene.size):
            slope = float(scene.slope_deg[nr, nc])
            roughness = float(scene.roughness[nr, nc])
            illumination = float(scene.illumination[nr, nc])
            communication = float(scene.communication[nr, nc])
            if slope > 25.0 or roughness > 0.88:
                continue
            hazard = 0.48 * np.clip(slope / 25.0, 0, 1) + 0.36 * roughness + 0.16 * (1 - communication)
            shadow_penalty = 1.05 * (1 - illumination)
            science_reward = 0.20 * float(ice.probability[nr, nc])
            move_cost = step * (1 + 2.4 * hazard * (1.15 - risk_tolerance) + shadow_penalty - science_reward)
            new_cost = cost_so_far[current] + max(0.15, move_cost)
            neighbour = (nr, nc)
            if new_cost < cost_so_far[neighbour]:
                cost_so_far[neighbour] = new_cost
                priority = new_cost + 1.15 * _heuristic(neighbour, goal)
                heapq.heappush(frontier, (priority, neighbour))
                came_from[neighbour] = current

    if goal not in came_from and goal != start:
        return TraversePlan(
            origin=origin,
            target=target,
            path=[origin],
            distance_m=0,
            estimated_energy_wh=0,
            duration_hours=0,
            mean_slope_deg=0,
            max_slope_deg=0,
            shadow_fraction=0,
            hazard_score=100,
            science_value=0,
            feasible=False,
            energy_margin_wh=battery_wh,
            rationale=["No traversable route was found under the selected terrain constraints."],
        )

    path_cells = [goal]
    while path_cells[-1] != start:
        path_cells.append(came_from[path_cells[-1]])
    path_cells.reverse()
    path = [GridPoint(row, col) for row, col in path_cells]

    distances = []
    for first, second in zip(path_cells, path_cells[1:]):
        distances.append(CELL_METERS * _heuristic(first, second))
    distance_m = float(sum(distances))
    rows = np.array([point[0] for point in path_cells], dtype=int)
    cols = np.array([point[1] for point in path_cells], dtype=int)
    slopes = scene.slope_deg[rows, cols]
    roughness = scene.roughness[rows, cols]
    illumination = scene.illumination[rows, cols]
    communication = scene.communication[rows, cols]

    terrain_factor = 1 + 0.045 * slopes.mean() + 0.8 * roughness.mean()
    thermal_factor = 1 + 0.24 * (illumination < 0.12).mean()
    energy_wh = distance_m * 0.82 * terrain_factor * thermal_factor
    duration = distance_m / max(speed_m_per_hour, 1)
    hazard = 100 * float(
        0.45 * np.clip(slopes.mean() / 20.0, 0, 1)
        + 0.32 * roughness.mean()
        + 0.14 * (1 - communication.mean())
        + 0.09 * (illumination < 0.12).mean()
    )
    science = 100 * float(0.68 * ice.probability[target.row, target.col] + 0.32 * ice.confidence[target.row, target.col])
    feasible = energy_wh <= battery_wh and slopes.max(initial=0) <= 25
    margin = battery_wh - energy_wh

    rationale = [
        f"Route targets a {science:.0f}/100 ice-evidence cell.",
        "Terrain cost balances slope, roughness, illumination and communications visibility.",
        f"Projected energy margin is {margin:.0f} Wh." if feasible else f"Projected energy deficit is {-margin:.0f} Wh.",
    ]
    return TraversePlan(
        origin=origin,
        target=target,
        path=path,
        distance_m=round(distance_m, 1),
        estimated_energy_wh=round(float(energy_wh), 1),
        duration_hours=round(float(duration), 2),
        mean_slope_deg=round(float(slopes.mean()), 2),
        max_slope_deg=round(float(slopes.max(initial=0)), 2),
        shadow_fraction=round(float((illumination < 0.12).mean()), 3),
        hazard_score=round(hazard, 2),
        science_value=round(science, 2),
        feasible=bool(feasible),
        energy_margin_wh=round(float(margin), 1),
        rationale=rationale,
    )
