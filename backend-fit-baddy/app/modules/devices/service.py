import random
import secrets
import uuid

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.modules.devices import models, schemas


def register_device(
    db: Session,
    user_id: int,
    name: str | None = None,
    device_id: str | None = None,
    kind: str = "simulator",
) -> models.Device:
    resolved_id = device_id or str(uuid.uuid4())
    existing = db.query(models.Device).filter(models.Device.device_id == resolved_id).first()
    if existing:
        return existing
    device = models.Device(
        device_id=resolved_id,
        device_token=secrets.token_hex(16),
        user_id=user_id,
        name=name or kind or "simulator",
        kind=kind or "simulator",
    )
    db.add(device)
    db.flush()
    return device


def get_or_create_simulator_device(db: Session, user_id: int) -> models.Device:
    device = (
        db.query(models.Device)
        .filter(models.Device.user_id == user_id)
        .order_by(models.Device.id)
        .first()
    )
    if device is None:
        device = register_device(db, user_id, "simulator")
    return device


def generate_sample() -> dict:
    return {
        "steps": random.randint(4000, 12000),
        "heart_rate": random.randint(62, 145),
        "calories": random.randint(180, 650),
        "timestamp": utc_now(),
        "source": "simulator",
    }


def store_sample(db: Session, user_id: int, device_id: str, sample: dict) -> models.TelemetryPoint:
    point = models.TelemetryPoint(
        device_id=device_id,
        user_id=user_id,
        steps=sample["steps"],
        heart_rate=sample["heart_rate"],
        calories=sample["calories"],
        timestamp=sample.get("timestamp") or utc_now(),
        source=sample.get("source") or "simulator",
    )
    db.add(point)
    db.flush()
    return point


def simulate_one(db: Session, user_id: int, overrides: dict | None = None) -> models.TelemetryPoint:
    device = get_or_create_simulator_device(db, user_id)
    sample = generate_sample()
    if overrides:
        for key in ("steps", "heart_rate", "calories"):
            if overrides.get(key) is not None:
                sample[key] = overrides[key]
    return store_sample(db, user_id, device.device_id, sample)


def get_latest(db: Session, user_id: int) -> models.TelemetryPoint | None:
    return (
        db.query(models.TelemetryPoint)
        .filter(models.TelemetryPoint.user_id == user_id)
        .order_by(models.TelemetryPoint.timestamp.desc())
        .first()
    )


def list_history(db: Session, user_id: int, limit: int = 50) -> list[models.TelemetryPoint]:
    return (
        db.query(models.TelemetryPoint)
        .filter(models.TelemetryPoint.user_id == user_id)
        .order_by(models.TelemetryPoint.timestamp.desc())
        .limit(limit)
        .all()
    )


def device_out(device: models.Device) -> schemas.DeviceRegisterOut:
    return schemas.DeviceRegisterOut(
        device_id=device.device_id,
        device_token=device.device_token,
        user_id=device.user_id,
        kind=device.kind,
        status="active",
    )
