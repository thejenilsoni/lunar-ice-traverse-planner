# API reference

The interactive OpenAPI explorer is available at `http://localhost:8000/docs`.

## Endpoints

- `GET /health` — service health.
- `GET /v1/scene?seed=2026&size=48` — complete scene, summary and grid layers.
- `POST /v1/ice/query` — evidence decomposition for one grid cell.
- `POST /v1/landing-sites/rank` — ranked safe landing-site candidates.
- `POST /v1/traverses/plan` — energy-aware rover route and mission diagnostics.

## Traverse request

```json
{
  "origin": {"row": 18, "col": 25},
  "target": null,
  "seed": 2026,
  "battery_wh": 2600,
  "speed_m_per_hour": 90,
  "risk_tolerance": 0.45
}
```

When `target` is omitted, the service selects the highest-utility reachable science cell outside the landing safety radius.
