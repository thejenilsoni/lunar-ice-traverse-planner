# Model card

**System:** LunaTraverse lunar ice and mobility baseline  
**Version:** `0.1.0`  
**Purpose:** transparent ice-evidence fusion, safe-site screening and rover-route prototyping

## Included methods

1. Deterministic lunar south-polar scene generator.
2. Physics-informed logistic evidence fusion.
3. Explicit roughness false-positive estimator.
4. Rule-constrained landing-site ranker.
5. Energy-aware A* traverse planner.

## Intended use

- hackathon and research prototyping;
- evaluation of data and product integration;
- relative comparison under a consistent scene snapshot;
- demonstration of explainable mission-planning workflows.

## Out-of-scope use

- declaring the presence or abundance of lunar ice;
- autonomous landing-site selection;
- commanding a rover;
- safety-critical navigation;
- publishing synthetic outputs as Chandrayaan-2 measurements.

## Limitations

The bundled scene, radar products, thermal field, communications field and energy model are synthetic. The evidence coefficients are not calibrated to a particular DFSAR product mode or incidence angle. Surface roughness, shadow geometry and rover energy are simplified.

## Production requirements

- calibrated PDS4 ingestion and geometry handling;
- independent science review of ice signatures;
- uncertainty propagation and probability calibration;
- validated DEM, illumination and communication products;
- rover-specific mobility and thermal-vacuum energy models;
- human approval of landing and traverse plans.
