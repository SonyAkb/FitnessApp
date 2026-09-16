from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.clock import utc_now
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    device_token = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False, default="simulator")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class TelemetryPoint(Base):
    __tablename__ = "telemetry_points"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    steps = Column(Integer, nullable=False)
    heart_rate = Column(Integer, nullable=False)
    calories = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    source = Column(String, nullable=False, default="simulator")
