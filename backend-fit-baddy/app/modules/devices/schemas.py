from datetime import datetime

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
    steps: int | None = None
    heart_rate: int | None = None
    calories: int | None = None
