"use client";

import { useMemo, useState, type CSSProperties } from "react";
import {
  buildLunarScene,
  formatNumber,
  planTraverse,
  rankLandingSites,
  sceneSummary,
} from "@/lib/lunar-engine.mjs";

type Layer = "ice" | "terrain" | "illumination" | "radar" | "risk";
type Cell = ReturnType<typeof buildLunarScene>["cells"][number];

const layers: Record<Layer, { label: string; detail: string }> = {
  ice: { label: "Ice probability", detail: "Fused DFSAR-style polarimetry, cold-trap and hydration evidence" },
  terrain: { label: "Terrain safety", detail: "Slope and surface roughness" },
  illumination: { label: "Illumination", detail: "Operational light and permanently shadowed regions" },
  radar: { label: "Radar evidence", detail: "L/S-band CPR and degree-of-polarization response" },
  risk: { label: "Traverse risk", detail: "Slope, roughness, darkness and communication exposure" },
};

function ramp(value: number, stops: [number, number, number][]) {
  const clamped = Math.max(0, Math.min(1, value));
  const scaled = clamped * (stops.length - 1);
  const lower = Math.floor(scaled);
  const upper = Math.min(stops.length - 1, lower + 1);
  const mix = scaled - lower;
  const color = stops[lower].map((channel, index) => Math.round(channel + (stops[upper][index] - channel) * mix));
  return `rgb(${color.join(",")})`;
}

function cellColor(cell: Cell, layer: Layer) {
  if (layer === "ice") return ramp(cell.iceProbability, [[12, 18, 31], [34, 75, 112], [62, 206, 203], [233, 249, 231]]);
  if (layer === "terrain") {
    const safety = 1 - Math.min(1, 0.62 * cell.slope / 22 + 0.38 * cell.roughness);
    return ramp(safety, [[151, 54, 49], [197, 128, 63], [117, 151, 111], [201, 221, 183]]);
  }
  if (layer === "illumination") return ramp(cell.illumination, [[5, 7, 14], [39, 46, 68], [128, 115, 97], [247, 226, 168]]);
  if (layer === "radar") return ramp(Math.max(0, Math.min(1, (cell.cprL - cell.dop - 0.25) / 1.15)), [[15, 20, 33], [62, 55, 103], [174, 76, 124], [255, 191, 105]]);
  const risk = Math.min(1, 0.48 * cell.slope / 25 + 0.34 * cell.roughness + 0.18 * (1 - cell.communication));
  return ramp(risk, [[44, 100, 91], [181, 143, 64], [177, 68, 62], [101, 24, 37]]);
}

function StatCard({ label, value, sub, accent }: { label: string; value: string; sub: string; accent: string }) {
  return (
    <article className="stat-card" style={{ "--accent": accent } as CSSProperties}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{sub}</small>
    </article>
  );
}

export function MissionConsole() {
  const scene = useMemo(() => buildLunarScene(2026, 36), []);
  const summary = useMemo(() => sceneSummary(scene), [scene]);
  const sites = useMemo(() => rankLandingSites(scene, 6), [scene]);
  const [layer, setLayer] = useState<Layer>("ice");
  const [siteId, setSiteId] = useState(sites[0].id);
  const [battery, setBattery] = useState(2600);
  const [riskTolerance, setRiskTolerance] = useState(45);
  const [selectedCellKey, setSelectedCellKey] = useState(scene.cells.findIndex((cell) => cell.row === 24 && cell.col === 25));
  const selectedSite = sites.find((site) => site.id === siteId) ?? sites[0];
  const traverse = useMemo(
    () => planTraverse(scene, selectedSite, null, { batteryWh: battery, riskTolerance: riskTolerance / 100 }),
    [scene, selectedSite, battery, riskTolerance],
  );
  const routeKeys = useMemo(() => new Set(traverse.path.map((cell) => `${cell.row}-${cell.col}`)), [traverse.path]);
  const selectedCell = scene.cells[selectedCellKey] ?? scene.cells[0];

  return (
    <main className="shell">
      <aside className="rail">
        <div className="mission-mark"><span>LT</span><i /></div>
        <nav>
          <button className="active" aria-label="Mission overview">◫<span>Mission</span></button>
          <button aria-label="Radar analysis">⌁<span>Radar</span></button>
          <button aria-label="Landing sites">⌖<span>Sites</span></button>
          <button aria-label="Traverse planning">↝<span>Traverse</span></button>
        </nav>
        <div className="rail-end"><b>CY2</b><small>South polar analogue</small></div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow"><span /> CHANDRAYAAN-2 MISSION ANALYTICS</p>
            <h1>LunaTraverse <em>Mission Console</em></h1>
          </div>
          <div className="top-actions">
            <div className="status"><i /> FUSION ENGINE ONLINE</div>
            <button className="export">Export mission plan</button>
          </div>
        </header>

        <div className="content-grid">
          <section className="primary-column">
            <div className="stat-grid">
              <StatCard label="High-confidence ice" value={`${summary.highIce}`} sub="30 m candidate cells" accent="#53d8cf" />
              <StatCard label="Permanent shadow" value={`${(summary.psrFraction * 100).toFixed(1)}%`} sub="of mapped scene" accent="#8793ff" />
              <StatCard label="Top site score" value={`${sites[0].score.toFixed(1)}`} sub={sites[0].id} accent="#f5bc69" />
              <StatCard label="Traverse margin" value={`${formatNumber(traverse.energyMargin, 0)} Wh`} sub={traverse.feasible ? "mission-feasible" : "energy deficit"} accent={traverse.feasible ? "#80d49d" : "#ff7a72"} />
            </div>

            <article className="map-card">
              <div className="card-heading">
                <div>
                  <p className="section-kicker">LUNAR SOUTH POLAR SECTOR • SYNTHETIC DEMONSTRATION</p>
                  <h2>{layers[layer].label}</h2>
                  <span>{layers[layer].detail}</span>
                </div>
                <div className="layer-tabs">
                  {(Object.keys(layers) as Layer[]).map((item) => (
                    <button key={item} className={item === layer ? "selected" : ""} onClick={() => setLayer(item)}>
                      {layers[item].label.split(" ")[0]}
                    </button>
                  ))}
                </div>
              </div>

              <div className="map-stage">
                <svg className="lunar-map" viewBox={`0 0 ${scene.size} ${scene.size}`} role="img" aria-label="Lunar south-polar mission map">
                  {scene.cells.map((cell, cellIndex) => {
                    const key = `${cell.row}-${cell.col}`;
                    return (
                      <rect
                        key={key}
                        x={cell.col}
                        y={cell.row}
                        width="1.03"
                        height="1.03"
                        fill={cellColor(cell, layer)}
                        className={cellIndex === selectedCellKey ? "selected-cell" : ""}
                        onClick={() => setSelectedCellKey(cellIndex)}
                      />
                    );
                  })}
                  {traverse.path.length > 1 && (
                    <polyline
                      points={traverse.path.map((cell) => `${cell.col + 0.5},${cell.row + 0.5}`).join(" ")}
                      fill="none"
                      stroke="#f8f4da"
                      strokeWidth="0.32"
                      strokeLinejoin="round"
                      strokeLinecap="round"
                      className="route-line"
                    />
                  )}
                  <circle cx={selectedSite.col + 0.5} cy={selectedSite.row + 0.5} r="0.65" className="landing-marker" />
                  <circle cx={traverse.target.col + 0.5} cy={traverse.target.row + 0.5} r="0.58" className="target-marker" />
                  {sites.slice(1).map((site) => (
                    <circle key={site.id} cx={site.col + 0.5} cy={site.row + 0.5} r="0.25" className="candidate-marker" />
                  ))}
                </svg>
                <div className="map-overlay top-left"><b>87.2°S</b><span>Faustini-inspired sector</span></div>
                <div className="map-overlay bottom-left"><i className="landing-dot" /> Landing site <i className="target-dot" /> Science target <i className="route-dot" /> Traverse</div>
                <div className="scale"><span /> 300 m</div>
              </div>

              <div className="map-footer">
                <div className="legend">
                  <span>LOW</span><i className={`legend-ramp ${layer}`} /><span>HIGH</span>
                </div>
                <div className="map-readout">Selected cell R{selectedCell.row} C{selectedCell.col} • {routeKeys.has(`${selectedCell.row}-${selectedCell.col}`) ? "ON TRAVERSE" : "ANALYSIS READY"}</div>
              </div>
            </article>

            <div className="lower-grid">
              <article className="panel candidate-panel">
                <div className="panel-title"><div><p>LANDING-SITE SHORTLIST</p><h3>Operationally safe access points</h3></div><span>{sites.length} candidates</span></div>
                <div className="site-list">
                  {sites.map((site, rank) => (
                    <button key={site.id} className={site.id === siteId ? "site-row active" : "site-row"} onClick={() => setSiteId(site.id)}>
                      <b>0{rank + 1}</b>
                      <div><strong>{site.id}</strong><span>{site.distance.toFixed(0)} m to ice evidence</span></div>
                      <em>{site.score.toFixed(1)}</em>
                      <i style={{ "--value": `${site.score}%` } as CSSProperties} />
                    </button>
                  ))}
                </div>
              </article>

              <article className="panel evidence-panel">
                <div className="panel-title"><div><p>SELECTED PIXEL</p><h3>Evidence decomposition</h3></div><span>R{selectedCell.row} C{selectedCell.col}</span></div>
                <div className="probability-ring" style={{ "--probability": `${selectedCell.iceProbability * 360}deg` } as CSSProperties}>
                  <div><strong>{(selectedCell.iceProbability * 100).toFixed(0)}%</strong><span>ice probability</span></div>
                </div>
                <div className="evidence-bars">
                  {[
                    ["L-band CPR", selectedCell.cprL / 1.6, selectedCell.cprL.toFixed(2)],
                    ["Low DOP signal", 1 - selectedCell.dop / 0.45, selectedCell.dop.toFixed(2)],
                    ["Cold-trap support", 1 - selectedCell.temperature / 145, `${selectedCell.temperature.toFixed(0)} K`],
                    ["Confidence", selectedCell.confidence, `${(selectedCell.confidence * 100).toFixed(0)}%`],
                  ].map(([label, value, display]) => (
                    <div key={label as string}><span>{label}</span><b>{display}</b><i><em style={{ width: `${Math.max(4, Number(value) * 100)}%` }} /></i></div>
                  ))}
                </div>
              </article>
            </div>
          </section>

          <aside className="inspector">
            <article className="panel mission-plan">
              <div className="panel-title"><div><p>MISSION PLAN</p><h3>{selectedSite.id} → Ice target</h3></div><span className={traverse.feasible ? "go" : "hold"}>{traverse.feasible ? "GO" : "HOLD"}</span></div>
              <div className="route-summary">
                <div><span>Distance</span><strong>{formatNumber(traverse.distance, 0)} m</strong></div>
                <div><span>Duration</span><strong>{traverse.duration.toFixed(1)} h</strong></div>
                <div><span>Energy</span><strong>{formatNumber(traverse.energyWh, 0)} Wh</strong></div>
                <div><span>Science value</span><strong>{traverse.science.toFixed(0)}/100</strong></div>
              </div>
              <div className="mission-path">
                <div><i className="landing-dot" /><span><b>{selectedSite.id}</b><small>Landing • {selectedSite.slope.toFixed(1)}° slope</small></span></div>
                <hr />
                <div><i className="waypoint-dot" /><span><b>{traverse.path.length} waypoints</b><small>{(traverse.shadowFraction * 100).toFixed(0)}% shadow exposure</small></span></div>
                <hr />
                <div><i className="target-dot" /><span><b>Radar target R{traverse.target.row} C{traverse.target.col}</b><small>{(traverse.target.iceProbability * 100).toFixed(0)}% ice probability</small></span></div>
              </div>
            </article>

            <article className="panel controls-panel">
              <div className="panel-title"><div><p>TRAVERSE CONTROLS</p><h3>Rover constraints</h3></div></div>
              <label><span>Battery capacity <b>{battery} Wh</b></span><input type="range" min="1400" max="5000" step="100" value={battery} onChange={(event) => setBattery(Number(event.target.value))} /></label>
              <label><span>Risk tolerance <b>{riskTolerance}%</b></span><input type="range" min="15" max="80" step="5" value={riskTolerance} onChange={(event) => setRiskTolerance(Number(event.target.value))} /></label>
              <div className="constraint-grid">
                <div><span>Mean slope</span><strong>{traverse.meanSlope.toFixed(1)}°</strong></div>
                <div><span>Maximum slope</span><strong>{traverse.maxSlope.toFixed(1)}°</strong></div>
                <div><span>Hazard score</span><strong>{traverse.hazard.toFixed(0)}/100</strong></div>
                <div><span>Energy margin</span><strong>{formatNumber(traverse.energyMargin, 0)} Wh</strong></div>
              </div>
            </article>

            <article className="panel explanation-panel">
              <div className="panel-title"><div><p>DECISION TRACE</p><h3>Why this route?</h3></div><span>auditable</span></div>
              <ul>
                <li><i>01</i><span>Starts from the highest-ranked safe landing ellipse with strong illumination and communication geometry.</span></li>
                <li><i>02</i><span>Avoids cells above 25° slope and heavily penalizes rough terrain, permanent darkness and weak links.</span></li>
                <li><i>03</i><span>Targets a high-value radar signature while preserving a projected {formatNumber(traverse.energyMargin, 0)} Wh reserve.</span></li>
              </ul>
            </article>

            <div className="science-boundary"><span>i</span><p><b>Scientific boundary</b> Radar signatures are probabilistic evidence. Candidate ice and routes require mission-team review, calibrated products and terrain validation before operational use.</p></div>
          </aside>
        </div>
      </section>
    </main>
  );
}
