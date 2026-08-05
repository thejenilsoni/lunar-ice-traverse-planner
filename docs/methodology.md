# Methodology

## 1. Radar and optical evidence fusion

The baseline combines:

- L-band Circular Polarization Ratio (CPR);
- S-band CPR;
- degree of polarization (DOP);
- L/S-band contrast as a shallow-subsurface cue;
- permanent-shadow and temperature context;
- hydration context;
- surface roughness and radar coherence as confounder indicators.

High CPR alone is not treated as proof of ice because rough blocky terrain can produce enhanced radar returns. The model increases probability when multiple independent signals agree and explicitly reports false-positive risk and confidence.

A 2026 ISRO-reported investigation of doubly shadowed craters highlighted high CPR together with low DOP as a refined volumetric-scattering criterion. The thresholds in this repository are illustrative and must be recalibrated against the selected DFSAR product mode, incidence angle and terrain context.

## 2. Landing-site suitability

A candidate must satisfy hard limits for slope, roughness, illumination and communication visibility. Survivors receive a weighted score across terrain safety, operational illumination, communication visibility, distance to high-confidence ice evidence and local science value.

The output is a ranked shortlist rather than a certification.

## 3. Traverse planning

The rover planner uses eight-connected A* search. Each movement cost includes path length, slope and roughness hazard, permanent-shadow exposure, communication visibility, configurable risk tolerance and a bounded science-value reward.

Cells above the hard slope or roughness threshold are excluded. The planner returns distance, energy, duration, maximum slope, shadow fraction, hazard, science value and energy margin.

## 4. Evaluation protocol

A field-grade evaluation should separately report:

- ice-detection precision, recall, calibration and spatial agreement against independently reviewed targets;
- false-positive rate over rough crater ejecta;
- landing-site ranking stability under product uncertainty;
- slope and roughness error against validated DEMs;
- route optimality, energy-model error and constraint-violation rate;
- robustness across incidence angles, product modes, seasons and lunar regions.

Synthetic validation metrics must never be presented as lunar-science performance.
