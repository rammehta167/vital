import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Event, Reading, Device, User
from ..schemas import SOSRequest, EventResponse
from ..security import get_optional_current_user
from ..services.notifications import dispatch_emergency_notifications
from ..services.audit import log_audit
from ..routers.stream import broadcast_event

router = APIRouter(prefix="/api/v1/sos", tags=["Emergency SOS"])


@router.post("", response_model=EventResponse)
async def trigger_manual_sos(
    sos_in: SOSRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    now = datetime.now(timezone.utc)
    user_id = current_user.id if current_user else None

    # Fallback to default patient if not authenticated
    if not user_id:
        def_patient = db.query(User).filter(User.role == "patient").first()
        if def_patient:
            user_id = def_patient.id

    # 1. Idempotency Check (Server-side 1-second debounce)
    if sos_in.idempotency_key:
        existing = db.query(Event).filter(Event.idempotency_key == sos_in.idempotency_key).first()
        if existing:
            # Check if within 5 seconds debounce window
            created_at = existing.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if (now - created_at).total_seconds() < 5.0:
                return existing

    # 2. Gather last 60 seconds of readings for telemetry snapshot
    sixty_secs_ago = now - timedelta(seconds=60)
    recent_readings = (
        db.query(Reading)
        .filter(Reading.measured_at >= sixty_secs_ago)
        .order_by(Reading.id.desc())
        .limit(30)
        .all()
    )

    vitals_summary = [
        {
            "bpm": r.bpm,
            "spo2": r.spo2,
            "temp_c": r.temp_c,
            "signal_quality": r.signal_quality,
            "measured_at": r.measured_at.isoformat()
        } for r in recent_readings
    ]

    # 3. Determine location (from payload or latest reading)
    lat = sos_in.lat
    lng = sos_in.lng
    if (lat is None or lng is None) and recent_readings:
        lat = recent_readings[0].lat
        lng = recent_readings[0].lng

    map_url = f"https://www.google.com/maps?q={lat},{lng}" if lat and lng else None

    # 4. Create Event
    ack_token = uuid.uuid4().hex
    idemp_key = sos_in.idempotency_key or f"sos_{int(now.timestamp())}_{uuid.uuid4().hex[:6]}"

    event = Event(
        user_id=user_id,
        device_id=sos_in.device_id or "ESP32-VITAL-01",
        event_type="sos_manual",
        severity="critical",
        status="created",
        title="EMERGENCY SOS: Panic Button Pressed",
        description=sos_in.details or "Manual panic alarm triggered by patient/hardware SOS button.",
        idempotency_key=idemp_key,
        lat=lat,
        lng=lng,
        map_url=map_url,
        vitals_snapshot=json.dumps(vitals_summary),
        ack_token=ack_token,
        created_at=now
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    log_audit(
        db, "SOS_TRIGGER", "Event",
        f"SOS alarm created (ID: {event.id}). Lat: {lat}, Lng: {lng}",
        user_id=user_id,
        actor_role="patient",
        ip_address=request.client.host if request.client else None
    )

    # 5. Dispatch multi-channel notifications
    dispatch_emergency_notifications(db, event)

    # 6. Stream SSE update
    await broadcast_event("event_created", {
        "id": event.id,
        "title": event.title,
        "status": event.status,
        "severity": event.severity,
        "event_type": event.event_type
    })

    return event
