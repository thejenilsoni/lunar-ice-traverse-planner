const CELL_METERS = 30;

function mulberry32(seed) {
  return function random() {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function normal(random) {
  const u = Math.max(random(), 1e-9);
  const v = Math.max(random(), 1e-9);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

const clamp = (value, low = 0, high = 1) => Math.max(low, Math.min(high, value));
const sigmoid = (value) => 1 / (1 + Math.exp(-value));
const index = (row, col, size) => row * size + col;

function crater(row, col, cy, cx, radius, depth) {
  const distance = Math.hypot(row - cy, col - cx);
  const bowl = -depth * Math.pow(clamp(1 - (distance / radius) ** 2), 1.7);
  const rim = depth * 0.18 * Math.exp(-((distance - radius) ** 2) / Math.max(1.4, radius * 0.14) ** 2);
  return bowl + rim;
}

export function buildLunarScene(seed = 2026, size = 36) {
  const random = mulberry32(seed);
  const cells = Array.from({ length: size * size }, (_, cellIndex) => {
    const row = Math.floor(cellIndex / size);
    const col = cellIndex % size;
    let elevation = 160 + 2.15 * col + 0.95 * row;
    const craters = [[10, 11, 6.8, 175], [24, 25, 8.4, 235], [28, 9, 5.2, 145], [13, 29, 4.6, 105]];
    for (const [cy, cx, radius, depth] of craters) elevation += crater(row, col, cy, cx, radius, depth);
    elevation += normal(random) * 3.2;
    return { row, col, elevation };
  });

  const elevations = cells.map((cell) => cell.elevation);
  const minElevation = Math.min(...elevations);
  const maxElevation = Math.max(...elevations);
  const elevationSpan = maxElevation - minElevation || 1;
  const getElevation = (row, col) => cells[index(clamp(row, 0, size - 1), clamp(col, 0, size - 1), size)].elevation;

  for (const cell of cells) {
    const gx = (getElevation(cell.row, cell.col + 1) - getElevation(cell.row, cell.col - 1)) / 60;
    const gy = (getElevation(cell.row + 1, cell.col) - getElevation(cell.row - 1, cell.col)) / 60;
    cell.slope = (Math.atan(Math.hypot(gx, gy)) * 180) / Math.PI;
    const neighbourMean = (getElevation(cell.row - 1, cell.col) + getElevation(cell.row + 1, cell.col) + getElevation(cell.row, cell.col - 1) + getElevation(cell.row, cell.col + 1)) / 4;
    cell.roughness = clamp(Math.abs(cell.elevation - neighbourMean) / 22 + 0.035 + normal(random) * 0.018);
    const depth = (maxElevation - cell.elevation) / elevationSpan;
    const incidence = clamp(0.18 + 0.8 * (0.36 * gx + 0.68 * gy), -1, 1);
    cell.illumination = clamp(0.44 + 0.34 * incidence - 0.57 * depth + normal(random) * 0.02);
    cell.psr = cell.illumination < 0.12;
    cell.temperature = clamp(32 + 92 * cell.illumination + 17 * (1 - depth), 24, 145);

    const deposits = [[10.5, 11, 3.8, 0.9], [24.5, 25, 4.7, 0.96], [28, 9, 2.6, 0.74]];
    let trueIce = 0;
    for (const [cy, cx, sigma, strength] of deposits) trueIce += strength * Math.exp(-((cell.row - cy) ** 2 + (cell.col - cx) ** 2) / (2 * sigma ** 2));
    trueIce *= clamp((0.23 - cell.illumination) / 0.23);
    const rock = clamp((cell.roughness - 0.42) * 1.9, 0, 0.75);
    cell.cprL = clamp(0.58 + 0.88 * trueIce + 0.52 * rock + normal(random) * 0.05, 0.15, 2.2);
    cell.cprS = clamp(0.56 + 0.55 * trueIce + 0.58 * rock + normal(random) * 0.05, 0.12, 2.1);
    cell.dop = clamp(0.34 - 0.27 * trueIce + 0.08 * rock + normal(random) * 0.016, 0.03, 0.58);
    cell.hydration = clamp(0.18 + 0.48 * trueIce + 0.15 * (1 - cell.illumination) + normal(random) * 0.03);
    cell.communication = clamp(0.28 + 0.62 * ((cell.elevation - minElevation) / elevationSpan) - 0.15 * clamp(cell.slope / 25));
    const falsePositive = clamp(0.62 * cell.roughness + 0.38 * (0.16 + 0.34 * cell.roughness + 0.21 * trueIce));
    const evidence = 0.88 * ((cell.cprL - 0.95) / 0.18) + 0.92 * ((0.16 - cell.dop) / 0.045) + 0.62 * ((cell.cprL - cell.cprS - 0.08) / 0.1) + 0.55 * ((78 - cell.temperature) / 16) + 0.38 * ((cell.hydration - 0.38) / 0.14) + (cell.psr ? 1.05 : 0) - 1.25 * falsePositive;
    cell.iceProbability = sigmoid(evidence);
    const agreement = ((cell.cprL > 1 ? 1 : 0) + (cell.dop < 0.16 ? 1 : 0) + (cell.temperature < 85 ? 1 : 0) + (cell.psr ? 1 : 0) + (cell.hydration > 0.42 ? 1 : 0)) / 5;
    cell.confidence = clamp(0.34 + 0.58 * agreement - 0.22 * falsePositive, 0.05, 0.98);
    cell.falsePositiveRisk = falsePositive;
  }
  return { seed, size, cells, cellMeters: CELL_METERS };
}

export function rankLandingSites(scene, limit = 6) {
  const targets = scene.cells.filter((cell) => cell.iceProbability >= 0.72 && cell.confidence >= 0.58);
  const nearestDistance = (cell) => targets.length ? Math.min(...targets.map((target) => Math.hypot(target.row - cell.row, target.col - cell.col))) * CELL_METERS : Infinity;
  const candidates = scene.cells.filter((cell) => cell.row > 1 && cell.col > 1 && cell.row < scene.size - 2 && cell.col < scene.size - 2 && cell.slope <= 14 && cell.roughness <= 0.58 && cell.illumination >= 0.16 && cell.communication >= 0.28).map((cell) => {
    const distance = nearestDistance(cell);
    const safety = clamp(1 - cell.slope / 16) * 0.55 + clamp(1 - cell.roughness) * 0.45;
    const science = 0.72 * Math.exp(-distance / 650) + 0.28 * cell.iceProbability;
    const operations = 0.56 * cell.illumination + 0.44 * cell.communication;
    return { id: `LS-${String(cell.row).padStart(2, "0")}${String(cell.col).padStart(2, "0")}`, ...cell, distance, safety, science, score: 100 * (0.48 * safety + 0.31 * operations + 0.21 * science) };
  }).sort((a, b) => b.score - a.score);
  const selected = [];
  for (const candidate of candidates) {
    if (selected.every((site) => Math.hypot(site.row - candidate.row, site.col - candidate.col) >= 4)) selected.push(candidate);
    if (selected.length >= limit) break;
  }
  return selected;
}

function neighbours(cell, size) {
  const result = [];
  for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [-1, 1], [1, -1], [1, 1]]) {
    const row = cell.row + dr;
    const col = cell.col + dc;
    if (row >= 0 && row < size && col >= 0 && col < size) result.push({ row, col, step: dr && dc ? Math.SQRT2 : 1 });
  }
  return result;
}

export function selectScienceTarget(scene, origin) {
  const reachable = new Set([index(origin.row, origin.col, scene.size)]);
  const queue = [origin];
  while (queue.length) {
    const current = queue.pop();
    for (const neighbour of neighbours(current, scene.size)) {
      const key = index(neighbour.row, neighbour.col, scene.size);
      if (reachable.has(key)) continue;
      const cell = scene.cells[key];
      if (cell.slope > 25 || cell.roughness > 0.88) continue;
      reachable.add(key);
      queue.push(cell);
    }
  }
  return scene.cells.reduce((best, cell) => {
    const key = index(cell.row, cell.col, scene.size);
    const distance = Math.hypot(cell.row - origin.row, cell.col - origin.col);
    if (!reachable.has(key) || cell.slope > 22 || distance < 3) return best;
    const utility = 0.72 * cell.iceProbability + 0.3 * cell.confidence + 0.15 * Math.exp(-distance / 15) - 0.26 * (clamp(cell.slope / 24) + 0.7 * cell.roughness);
    return !best || utility > best.utility ? { ...cell, utility } : best;
  }, null) ?? origin;
}

export function planTraverse(scene, origin, target = null, options = {}) {
  const destination = target ?? selectScienceTarget(scene, origin);
  const batteryWh = options.batteryWh ?? 2200;
  const riskTolerance = options.riskTolerance ?? 0.45;
  const speed = options.speed ?? 90;
  const startKey = index(origin.row, origin.col, scene.size);
  const goalKey = index(destination.row, destination.col, scene.size);
  const frontier = [{ key: startKey, priority: 0 }];
  const costs = new Map([[startKey, 0]]);
  const cameFrom = new Map();
  const byKey = (key) => scene.cells[key];
  while (frontier.length) {
    frontier.sort((a, b) => a.priority - b.priority);
    const currentKey = frontier.shift().key;
    if (currentKey === goalKey) break;
    const current = byKey(currentKey);
    for (const neighbour of neighbours(current, scene.size)) {
      const next = scene.cells[index(neighbour.row, neighbour.col, scene.size)];
      if (next.slope > 25 || next.roughness > 0.88) continue;
      const hazard = 0.48 * clamp(next.slope / 25) + 0.36 * next.roughness + 0.16 * (1 - next.communication);
      const moveCost = neighbour.step * (1 + 2.4 * hazard * (1.15 - riskTolerance) + 1.05 * (1 - next.illumination) - 0.2 * next.iceProbability);
      const nextKey = index(next.row, next.col, scene.size);
      const newCost = costs.get(currentKey) + Math.max(0.15, moveCost);
      if (!costs.has(nextKey) || newCost < costs.get(nextKey)) {
        costs.set(nextKey, newCost);
        cameFrom.set(nextKey, currentKey);
        frontier.push({ key: nextKey, priority: newCost + 1.15 * Math.hypot(next.row - destination.row, next.col - destination.col) });
      }
    }
  }
  if (!cameFrom.has(goalKey) && goalKey !== startKey) return { feasible: false, path: [origin], target: destination, hazard: 100, energyWh: 0, distance: 0 };
  const keys = [goalKey];
  while (keys[0] !== startKey) keys.unshift(cameFrom.get(keys[0]));
  const path = keys.map(byKey);
  let distance = 0;
  for (let i = 1; i < path.length; i += 1) distance += CELL_METERS * Math.hypot(path[i].row - path[i - 1].row, path[i].col - path[i - 1].col);
  const mean = (field) => path.reduce((sum, cell) => sum + cell[field], 0) / path.length;
  const meanSlope = mean("slope");
  const meanRoughness = mean("roughness");
  const shadowFraction = path.filter((cell) => cell.illumination < 0.12).length / path.length;
  const energyWh = distance * 0.82 * (1 + 0.045 * meanSlope + 0.8 * meanRoughness) * (1 + 0.24 * shadowFraction);
  const hazard = 100 * (0.45 * clamp(meanSlope / 20) + 0.32 * meanRoughness + 0.14 * (1 - mean("communication")) + 0.09 * shadowFraction);
  const science = 100 * (0.68 * destination.iceProbability + 0.32 * destination.confidence);
  return { feasible: energyWh <= batteryWh, path, target: destination, distance, energyWh, energyMargin: batteryWh - energyWh, duration: distance / speed, meanSlope, maxSlope: Math.max(...path.map((cell) => cell.slope)), shadowFraction, hazard, science };
}

export function sceneSummary(scene) {
  const highIce = scene.cells.filter((cell) => cell.iceProbability >= 0.72 && cell.confidence >= 0.62);
  const psr = scene.cells.filter((cell) => cell.psr);
  return { highIce: highIce.length, psrFraction: psr.length / scene.cells.length, meanSlope: scene.cells.reduce((sum, cell) => sum + cell.slope, 0) / scene.cells.length, maxIce: Math.max(...scene.cells.map((cell) => cell.iceProbability)) };
}

export const formatNumber = (value, digits = 1) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: digits }).format(value);
