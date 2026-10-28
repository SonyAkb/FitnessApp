from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegisterIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    device_id: str | None = None
    kind: str = "simulator"


class DeviceRegisterOut(BaseModel):
    device_id: str
    device_token: str
    user_id: int
    kind: str = "simulator"
    status: str = "active"


class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    user_id: int
    steps: int
    heart_rate: int
    calories: int
    timestamp: datetime
    source: str


class TelemetrySimulateIn(BaseModel):
    steps: int | None = Field(default=None, ge=0)
    heart_rate: int | None = Field(default=None, ge=0, le=250)
    calories: int | None = Field(default=None, ge=0)


# Pulse range accepted from real sensors (the Pi publisher filters by the same bounds).
HEART_RATE_MIN = 30
HEART_RATE_MAX = 230


class TelemetryIngestIn(BaseModel):
    """TelemetryDTO from a paired device, without user_id: the user comes from the device token."""

    device_id: str = Field(min_length=1, max_length=80)
    steps: int = Field(ge=0)
    heart_rate: int = Field(ge=HEART_RATE_MIN, le=HEART_RATE_MAX)
    calories: int = Field(default=0, ge=0)
    timestamp: datetime
    source: str | None = None


class TelemetryPointIn(BaseModel):
    steps: int = Field(ge=0)
    heart_rate: int = Field(ge=HEART_RATE_MIN, le=HEART_RATE_MAX)
    calories: int = Field(default=0, ge=0)
    timestamp: datetime


class TelemetryBatchIn(BaseModel):
    """Points the app read from Health Connect (steps and pulse written there by watches and bands)."""

    source: Literal["health_connect"] = "health_connect"
    points: list[TelemetryPointIn] = Field(min_length=1, max_length=500)


class TelemetryBatchOut(BaseModel):
    device_id: str
    accepted: int
    duplicates: int


class PairingCodeIn(BaseModel):
    kind: Literal["raspberry_pi"] = "raspberry_pi"
    name: str | None = Field(default=None, min_length=1, max_length=80)


class PairingCodeOut(BaseModel):
    code: str
    kind: str
    expires_at: datetime


class PairIn(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")
    device_id: str = Field(min_length=1, max_length=80)


class DeviceOut(BaseModel):
    device_id: str
    name: str
    kind: str
    created_at: datetime
    last_seen_at: datetime | None = None
