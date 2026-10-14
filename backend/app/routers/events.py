from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Event, EventLog, User
from ..schemas import EventResponse, EventResolveRequest, MessageResponse
from ..security import get_optional_current_user, get_current_user
from ..services.warning_engine import cancel_pending_candidate
from ..services.audit import log_audit
from ..routers.stream import broadcast_event

router = APIRouter(prefix="/api/v1/events", tags=["Emergency Events & Alerts"])


@router.get("", response_model=List[EventResponse])
def list_events(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if severity:
        query = query.filter(Event.severity == severity)
    if status:
        query = query.filter(Event.status == status)

    events = query.order_by(Event.id.desc()).limit(limit).all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/ack/{ack_token}")
async def acknowledge_event_by_token(
    ack_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.ack_token == ack_token).first()
    if not event:
        raise HTTPException(status_code=404, detail="Invalid or expired acknowledgement token")

    now = datetime.now(timezone.utc)
    if event.status != "acknowledged" and event.status != "resolved":
        event.status = "acknowledged"
        event.acknowledged_at = now
        event.acknowledged_by = "Emergency Responder / Contact via Link"

        log = EventLog(
            event_id=event.id,
            status="acknowledged",
            channel="web_link",
            detail=f"Acknowledged by responder from IP: {request.client.host if request.client else 'Unknown'}",
            created_at=now
        )
        db.add(log)
        db.commit()
        db.refresh(event)

        log_audit(db, "EVENT_ACK", "Event", f"Event #{event.id} acknowledged by token", user_id=event.user_id, ip_address=request.client.host if request.client else None)

        await broadcast_event("event_updated", {
            "id": event.id,
            "status": "acknowledged",
            "title": event.title
        })

    return {
        "message": "Emergency alert successfully acknowledged. Emergency response dispatched.",
        "event_id": event.id,
        "title": event.title,
        "severity": event.severity,
        "status": event.status,
        "acknowledged_at": event.acknowledged_at.isoformat() if event.acknowledged_at else None
    }


@router.post("/{event_id}/resolve", response_model=EventResponse)
async def resolve_event(
    event_id: int,
    resolve_in: EventResolveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    now = datetime.now(timezone.utc)
    event.status = "resolved"
    event.resolved_at = now
    resolver_name = resolve_in.resolved_by or (current_user.full_name if current_user else "User")
    event.resolved_by = resolver_name

    log = EventLog(
        event_id=event.id,
        status="resolved",
        channel="in_app",
        detail=f"Resolved by {resolver_name}. Notes: {resolve_in.notes or 'None'}",
        created_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(event)

    log_audit(db, "EVENT_RESOLVE", "Event", f"Event #{event.id} marked as resolved by {resolver_name}", user_id=event.user_id, ip_address=request.client.host if request.client else None)

    await broadcast_event("event_updated", {
        "id": event.id,
        "status": "resolved",
        "title": event.title
    })

    return event


@router.post("/cancel-warning/{candidate_id}", response_model=MessageResponse)
async def cancel_automatic_warning(
    candidate_id: str,
    device_id: Optional[str] = "ESP32-VITAL-01",
    db: Session = Depends(get_db)
):
    success = cancel_pending_candidate(device_id, candidate_id)
    if success:
        await broadcast_event("auto_warning_cancelled", {"candidate_id": candidate_id, "device_id": device_id})
        return {
            "message": "Automatic warning cancelled by user during grace countdown.",
            "detail": f"Candidate ID {candidate_id} dismissed."
        }
    else:
        return {
            "message": "Candidate not found or already processed.",
            "detail": candidate_id
        }
