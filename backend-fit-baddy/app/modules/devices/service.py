import random
import secrets
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.modules.devices import models, schemas


# Kinds of devices that bring real measurements; the WebSocket simulates only for users without them.
REAL_DEVICE_KINDS = ("raspberry_pi", "health_connect")
PAIRING_CODE_TTL = timedelta(minutes=10)


class DeviceOwnedByAnotherUser(Exception):
    """The device_id is already registered to a different user."""


class PairingCodeInvalid(Exception):
    """The pairing code is unknown, already used or expired."""


def find_device(db: Session, device_id: str) -> models.Device | None:
    return db.query(models.Device).filter(models.Device.device_id == device_id).first()


def register_device(
    db: Session,
    user_id: int,
    name: str | None = None,
    device_id: str | None = None,
    kind: str = "simulator",
) -> models.Device:
    resolved_id = device_id or str(uuid.uuid4())
    existing = find_device(db, resolved_id)
    if existing:
        if existing.user_id != user_id:
            raise DeviceOwnedByAnotherUser(resolved_id)
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
        .filter(models.Device.user_id == user_id, models.Device.kind == "simulator")
        .order_by(models.Device.id)
        .first()
    )
    if device is None:
        device = register_device(db, user_id, "simulator")
    return device


def find_device_by_token(db: Session, token: str) -> models.Device | None:
    return db.query(models.Device).filter(models.Device.device_token == token).first()


def has_real_device(db: Session, user_id: int) -> bool:
    return (
        db.query(models.Device.id)
        .filter(models.Device.user_id == user_id, models.Device.kind.in_(REAL_DEVICE_KINDS))
        .first()
        is not None
    )


def list_devices(db: Session, user_id: int) -> list[schemas.DeviceOut]:
    last_seen = (
        db.query(models.TelemetryPoint.device_id, func.max(models.TelemetryPoint.timestamp).label("last_seen"))
        .filter(models.TelemetryPoint.user_id == user_id)
        .group_by(models.TelemetryPoint.device_id)
        .subquery()
    )
    rows = (
        db.query(models.Device, last_seen.c.last_seen)
        .outerjoin(last_seen, last_seen.c.device_id == models.Device.device_id)
        .filter(models.Device.user_id == user_id)
        .order_by(models.Device.id)
        .all()
    )
    return [
        schemas.DeviceOut(device_id=d.device_id, name=d.name, kind=d.kind, created_at=d.created_at, last_seen_at=seen)
        for d, seen in rows
    ]


def delete_device(db: Session, user_id: int, device_id: str) -> bool:
    """Unlink a device: its token stops working, already received points stay in the history."""
    device = find_device(db, device_id)
    if device is None or device.user_id != user_id:
        return False
    db.delete(device)
    db.flush()
    return True


# --- pairing by a short code -------------------------------------------------
# The app asks for a code, the Pi node exchanges it for its own token. Codes live in
# process memory for PAIRING_CODE_TTL: enough for a single backend process (docker compose).


@dataclass
class _Pairing:
    user_id: int
    kind: str
    name: str | None
    expires_at: datetime


_pairings: dict[str, _Pairing] = {}
_pairings_lock = threading.Lock()


def create_pairing_code(user_id: int, kind: str = "raspberry_pi", name: str | None = None) -> tuple[str, datetime]:
    now = utc_now()
    with _pairings_lock:
        for code in [c for c, p in _pairings.items() if p.user_id == user_id or p.expires_at <= now]:
            del _pairings[code]  # one active code per user
        code = f"{secrets.randbelow(10**6):06d}"
        while code in _pairings:
            code = f"{secrets.randbelow(10**6):06d}"
        expires_at = now + PAIRING_CODE_TTL
        _pairings[code] = _Pairing(user_id=user_id, kind=kind, name=name, expires_at=expires_at)
    return code, expires_at


def pair_device(db: Session, code: str, device_id: str) -> models.Device:
    """Exchange a pairing code for a device registered to the code's user (code is single-use)."""
    with _pairings_lock:
        pairing = _pairings.get(code)
        if pairing is None or pairing.expires_at <= utc_now():
            _pairings.pop(code, None)
            raise PairingCodeInvalid(code)
        existing = find_device(db, device_id)
        if existing is not None and existing.user_id != pairing.user_id:
            raise DeviceOwnedByAnotherUser(device_id)
        del _pairings[code]
    if existing is not None:
        existing.device_token = secrets.token_hex(16)  # re-pairing issues a fresh token
        existing.kind = pairing.kind
        db.flush()
        return existing
    return register_device(db, pairing.user_id, name=pairing.name or "Raspberry Pi", device_id=device_id, kind=pairing.kind)


def reset_pairings() -> None:
    with _pairings_lock:
        _pairings.clear()


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


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def find_point(db: Session, device_id: str, timestamp: datetime) -> models.TelemetryPoint | None:
    return (
        db.query(models.TelemetryPoint)
        .filter(models.TelemetryPoint.device_id == device_id, models.TelemetryPoint.timestamp == timestamp)
        .first()
    )


def ingest_point(db: Session, device: models.Device, data: schemas.TelemetryIngestIn) -> tuple[models.TelemetryPoint, bool]:
    """Store a point from a paired device; a repeated (device_id, timestamp) is not stored twice.

    Returns the point and whether it was created now.
    """
    timestamp = _as_utc(data.timestamp)
    existing = find_point(db, device.device_id, timestamp)
    if existing is not None:
        return existing, False
    sample = {"steps": data.steps, "heart_rate": data.heart_rate, "calories": data.calories,
              "timestamp": timestamp, "source": device.kind}
    return store_sample(db, device.user_id, device.device_id, sample), True


def get_or_create_health_connect_device(db: Session, user_id: int) -> models.Device:
    return register_device(db, user_id, name="Health Connect", device_id=f"health-connect-{user_id}", kind="health_connect")


def ingest_batch(db: Session, user_id: int, data: schemas.TelemetryBatchIn) -> schemas.TelemetryBatchOut:
    device = get_or_create_health_connect_device(db, user_id)
    accepted = duplicates = 0
    seen: set[datetime] = set()
    for item in sorted(data.points, key=lambda p: _as_utc(p.timestamp)):
        timestamp = _as_utc(item.timestamp)
        if timestamp in seen or find_point(db, device.device_id, timestamp) is not None:
            duplicates += 1
            continue
        seen.add(timestamp)
        store_sample(db, user_id, device.device_id, {"steps": item.steps, "heart_rate": item.heart_rate,
                                                     "calories": item.calories, "timestamp": timestamp,
                                                     "source": "health_connect"})
        accepted += 1
    return schemas.TelemetryBatchOut(device_id=device.device_id, accepted=accepted, duplicates=duplicates)


def points_after(db: Session, user_id: int, after_id: int, limit: int = 50) -> list[models.TelemetryPoint]:
    """New points of the user in arrival order — what the WebSocket streams."""
    return (
        db.query(models.TelemetryPoint)
        .filter(models.TelemetryPoint.user_id == user_id, models.TelemetryPoint.id > after_id)
        .order_by(models.TelemetryPoint.id)
        .limit(limit)
        .all()
    )


def latest_point_id(db: Session, user_id: int) -> int:
    value = db.query(func.max(models.TelemetryPoint.id)).filter(models.TelemetryPoint.user_id == user_id).scalar()
    return value or 0


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


def list_history(
    db: Session,
    user_id: int,
    limit: int = 50,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[models.TelemetryPoint]:
    query = db.query(models.TelemetryPoint).filter(models.TelemetryPoint.user_id == user_id)
    if date_from is not None:
        query = query.filter(models.TelemetryPoint.timestamp >= date_from)
    if date_to is not None:
        query = query.filter(models.TelemetryPoint.timestamp <= date_to)
    return query.order_by(models.TelemetryPoint.timestamp.desc()).limit(limit).all()


def device_out(device: models.Device) -> schemas.DeviceRegisterOut:
    return schemas.DeviceRegisterOut(
        device_id=device.device_id,
        device_token=device.device_token,
        user_id=device.user_id,
        kind=device.kind,
        status="active",
    )
