import assert from "node:assert/strict";
import test from "node:test";

import { buildLunarScene, planTraverse, rankLandingSites, sceneSummary } from "../lib/lunar-engine.mjs";

test("scene generation is deterministic", () => {
  const first = buildLunarScene(2026, 36);
  const second = buildLunarScene(2026, 36);
  assert.equal(first.cells[500].iceProbability, second.cells[500].iceProbability);
  assert.equal(first.cells.length, 1296);
});

test("scene contains polar shadow and ice evidence", () => {
  const summary = sceneSummary(buildLunarScene());
  assert.ok(summary.psrFraction > 0.03);
  assert.ok(summary.highIce > 0);
  assert.ok(summary.maxIce > 0.8);
});

test("landing sites satisfy operational constraints", () => {
  const scene = buildLunarScene();
  const sites = rankLandingSites(scene, 6);
  assert.equal(sites.length, 6);
  assert.ok(sites.every((site) => site.slope <= 14 && site.roughness <= 0.58));
});

test("traverse planner returns a route and energy estimate", () => {
  const scene = buildLunarScene();
  const origin = rankLandingSites(scene, 1)[0];
  const plan = planTraverse(scene, origin, null, { batteryWh: 5000 });
  assert.ok(plan.path.length > 1);
  assert.ok(plan.distance > 0);
  assert.ok(plan.energyWh > 0);
  assert.equal(plan.feasible, true);
});
