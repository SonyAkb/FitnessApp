import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.devices import schemas, service

router = APIRouter(tags=["devices & telemetry"])


@router.post("/devices/register", response_model=schemas.DeviceRegisterOut, status_code=status.HTTP_201_CREATED)
def register_device(
    data: schemas.DeviceRegisterIn,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    already_registered = data.device_id is not None and service.find_device(db, data.device_id) is not None
    try:
        device = service.register_device(
            db,
            current_user.id,
            name=data.name,
            device_id=data.device_id,
            kind=data.kind,
        )
    except service.DeviceOwnedByAnotherUser:
        raise HTTPException(status_code=409, detail="Device is registered to another user")
    db.commit()
    db.refresh(device)
    if already_registered:
        response.status_code = status.HTTP_200_OK
    return service.device_out(device)


@router.get("/devices", response_model=list[schemas.DeviceOut])
def list_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.list_devices(db, current_user.id)


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not service.delete_device(db, current_user.id, device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/devices/pairing", response_model=schemas.PairingCodeOut, status_code=status.HTTP_201_CREATED)
def create_pairing_code(
    data: schemas.PairingCodeIn | None = Body(default=None),
    current_user: User = Depends(get_current_user),
):
    data = data or schemas.PairingCodeIn()
    code, expires_at = service.create_pairing_code(current_user.id, kind=data.kind, name=data.name)
    return schemas.PairingCodeOut(code=code, kind=data.kind, expires_at=expires_at)


@router.post("/devices/pair", response_model=schemas.DeviceRegisterOut)
def pair_device(data: schemas.PairIn, db: Session = Depends(get_db)):
    """Called by the device itself (no user token): exchanges the code shown in the app for a device token."""
    try:
        device = service.pair_device(db, data.code, data.device_id)
    except service.PairingCodeInvalid:
        raise HTTPException(status_code=404, detail="Pairing code is invalid or expired")
    except service.DeviceOwnedByAnotherUser:
        raise HTTPException(status_code=409, detail="Device is registered to another user")
    db.commit()
    db.refresh(device)
    return service.device_out(device)


@router.post("/telemetry/ingest", response_model=schemas.TelemetryOut, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(
    data: schemas.TelemetryIngestIn,
    response: Response,
    x_device_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """A point from a paired device (Raspberry Pi). Repeating the same point returns it with 200."""
    device = service.find_device_by_token(db, x_device_token) if x_device_token else None
    if device is None:
        raise HTTPException(status_code=401, detail="Invalid device token")
    if device.device_id != data.device_id:
        raise HTTPException(status_code=403, detail="Token does not belong to this device")
    point, created = service.ingest_point(db, device, data)
    db.commit()
    db.refresh(point)
    if not created:
        response.status_code = status.HTTP_200_OK
    return point


@router.post("/telemetry/batch", response_model=schemas.TelemetryBatchOut)
def ingest_batch(
    data: schemas.TelemetryBatchIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Points read by the app from Health Connect; already received timestamps are skipped."""
    result = service.ingest_batch(db, current_user.id, data)
    db.commit()
    return result


@router.get("/telemetry/latest", response_model=schemas.TelemetryOut)
def latest_telemetry(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    point = service.get_latest(db, current_user.id)
    if point is None:
        raise HTTPException(status_code=404, detail="No telemetry yet")
    return point


@router.get("/telemetry/history", response_model=list[schemas.TelemetryOut])
def telemetry_history(
    limit: int = Query(default=50, ge=1, le=200),
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_history(db, current_user.id, limit=limit, date_from=date_from, date_to=date_to)


@router.post("/telemetry/simulate", response_model=schemas.TelemetryOut, status_code=status.HTTP_201_CREATED)
def simulate_telemetry(
    data: schemas.TelemetrySimulateIn | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    overrides = data.model_dump(exclude_unset=True) if data else None
    point = service.simulate_one(db, current_user.id, overrides=overrides)
    db.commit()
    db.refresh(point)
    return point


@router.websocket("/telemetry/ws")
async def telemetry_ws(websocket: WebSocket, token: str | None = None):
    await websocket.accept()
    raw_token = token
    try:
        if not raw_token:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.close(code=4400)
                return
            raw_token = payload.get("token") if isinstance(payload, dict) else None
        user_id = decode_access_token(raw_token) if raw_token else None
        if user_id is None:
            await websocket.close(code=4401)
            return
        uid = int(user_id)
        db = SessionLocal()
        try:
            # Start from the latest stored point so the client sees the current value right away.
            last_id = max(service.latest_point_id(db, uid) - 1, 0)
        finally:
            db.close()
        while True:
            db = SessionLocal()
            try:
                # Without a real device (Pi, Health Connect) the demo keeps working on the simulator.
                if not service.has_real_device(db, uid):
                    service.simulate_one(db, uid)
                    db.commit()
                for point in service.points_after(db, uid, last_id):
                    body = schemas.TelemetryOut.model_validate(point)
                    await websocket.send_json(jsonable_encoder(body))
                    last_id = point.id
            finally:
                db.close()
            await asyncio.sleep(settings.TELEMETRY_WS_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close()
        except Exception:
            return
