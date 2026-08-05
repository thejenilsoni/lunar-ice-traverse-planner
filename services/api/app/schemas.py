from __future__ import annotations

from pydantic import BaseModel, Field


class PointRequest(BaseModel):
    row: int = Field(ge=0, le=127)
    col: int = Field(ge=0, le=127)


class TraverseRequest(BaseModel):
    origin: PointRequest
    target: PointRequest | None = None
    seed: int = 2026
    battery_wh: float = Field(default=2200, gt=100, le=20000)
    speed_m_per_hour: float = Field(default=90, gt=5, le=500)
    risk_tolerance: float = Field(default=0.45, ge=0, le=1)


class LandingRequest(BaseModel):
    seed: int = 2026
    limit: int = Field(default=8, ge=1, le=20)


class IceQuery(BaseModel):
    row: int = Field(ge=0, le=127)
    col: int = Field(ge=0, le=127)
    seed: int = 2026
