import asyncio
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = service.register_device(
        db,
        current_user.id,
        name=data.name,
        device_id=data.device_id,
        kind=data.kind,
    )
    db.commit()
    db.refresh(device)
    return service.device_out(device)


@router.get("/telemetry/latest", response_model=schemas.TelemetryOut)
def latest_telemetry(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    point = service.get_latest(db, current_user.id)
    if point is None:
        raise HTTPException(status_code=404, detail="No telemetry yet")
    return point


@router.get("/telemetry/history", response_model=list[schemas.TelemetryOut])
def telemetry_history(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_history(db, current_user.id, limit=limit)


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
        while True:
            db = SessionLocal()
            try:
                point = service.simulate_one(db, uid)
                db.commit()
                db.refresh(point)
                body = schemas.TelemetryOut.model_validate(point)
                await websocket.send_json(jsonable_encoder(body))
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
