import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from ..models import Reading, Event, Device
from ..services.notifications import dispatch_emergency_notifications
from ..routers.stream import broadcast_event

# Configurable limits (educational examples, not clinical rules)
LIMITS = {
    "bpm_min": 50.0,
    "bpm_max": 120.0,
    "spo2_min": 92.0,
    "temp_max": 38.0
}

# State tracker per device_id
# device_id -> {"abnormal_streak": [datetime], "last_warning_at": datetime, "pending_candidate": dict}
_DEVICE_TRACKERS: Dict[str, Dict[str, Any]] = {}


def get_current_limits() -> Dict[str, float]:
    return LIMITS.copy()


def update_limits(new_limits: Dict[str, float]):
    global LIMITS
    for k, v in new_limits.items():
        if k in LIMITS and isinstance(v, (int, float)):
            LIMITS[k] = float(v)


def is_abnormal(bpm: Optional[float], spo2: Optional[float], temp_c: Optional[float]) -> tuple:
    reasons = []
    if bpm is not None:
        if bpm < LIMITS["bpm_min"]:
            reasons.append(f"Low pulse ({bpm:.0f} < {LIMITS['bpm_min']:.0f} BPM)")
        elif bpm > LIMITS["bpm_max"]:
            reasons.append(f"High pulse ({bpm:.0f} > {LIMITS['bpm_max']:.0f} BPM)")
    if spo2 is not None and spo2 < LIMITS["spo2_min"]:
        reasons.append(f"Low oxygen ({spo2:.0f}% < {LIMITS['spo2_min']:.0f}%)")
    if temp_c is not None and temp_c > LIMITS["temp_max"]:
        reasons.append(f"Elevated temperature ({temp_c:.1f}°C > {LIMITS['temp_max']:.1f}°C)")

    return (len(reasons) > 0, ", ".join(reasons))


async def evaluate_reading_for_warning(
    db: Session,
    reading: Reading,
    user_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Evaluates reading for automatic warning.
    Criteria:
    - Signal quality MUST be 'good'
    - Reading MUST be valid
    - Readings outside limits consecutively for >= 30 seconds
    """
    device_id = reading.device_id
    if device_id not in _DEVICE_TRACKERS:
        _DEVICE_TRACKERS[device_id] = {
            "abnormal_streak": [],
            "last_warning_at": None,
            "pending_candidate": None
        }

    tracker = _DEVICE_TRACKERS[device_id]

    # If poor signal, noisy, or no finger, reset abnormal streak
    if reading.signal_quality != "good" or not reading.is_valid:
        tracker["abnormal_streak"] = []
        return None

    abnormal, reason = is_abnormal(reading.bpm, reading.spo2, reading.temp_c)

    if not abnormal:
        tracker["abnormal_streak"] = []
        return None

    now = reading.measured_at or datetime.now(timezone.utc)
    tracker["abnormal_streak"].append((now, reason))

    # Clean streak older than 60s
    streak = tracker["abnormal_streak"]
    if len(streak) < 2:
        return None

    first_time, first_reason = streak[0]
    duration_secs = (now - first_time).total_seconds()

    # Need >= 30 seconds of sustained abnormal readings
    if duration_secs >= 30.0:
        # Check cooldown (don't re-trigger warning within 60s of last warning)
        last_warn = tracker["last_warning_at"]
        if last_warn and (now - last_warn).total_seconds() < 60.0:
            return None

        # Check if candidate is already in grace countdown
        candidate = tracker.get("pending_candidate")
        if candidate and candidate.get("status") == "countdown":
            return None

        candidate_id = f"cand_{device_id}_{int(time.time())}"
        candidate_data = {
            "candidate_id": candidate_id,
            "device_id": device_id,
            "user_id": user_id,
            "reason": reason,
            "duration_secs": round(duration_secs, 1),
            "countdown_seconds": 15,
            "status": "countdown",
            "lat": reading.lat,
            "lng": reading.lng,
            "bpm": reading.bpm,
            "spo2": reading.spo2,
            "temp_c": reading.temp_c
        }
        tracker["pending_candidate"] = candidate_data
        tracker["last_warning_at"] = now
        tracker["abnormal_streak"] = []  # Reset streak

        # Broadcast countdown event to UI
        await broadcast_event("auto_warning_countdown", candidate_data)

        # Launch background task for 15s grace period
        asyncio.create_task(_resolve_candidate_after_countdown(candidate_id, device_id, user_id))

        return candidate_data

    return None


async def _resolve_candidate_after_countdown(candidate_id: str, device_id: str, user_id: Optional[int]):
    """Wait 15s grace countdown. If not cancelled, commit automatic unconfirmed warning."""
    await asyncio.sleep(15.0)

    tracker = _DEVICE_TRACKERS.get(device_id)
    if not tracker:
        return

    candidate = tracker.get("pending_candidate")
    if not candidate or candidate.get("candidate_id") != candidate_id:
        return

    # If it was cancelled by user, it won't be in 'countdown'
    if candidate.get("status") != "countdown":
        return

    # Candidate was NOT cancelled: create automatic warning event
    from ..db import SessionLocal
    db = SessionLocal()
    try:
        import uuid
        import json
        event = Event(
            user_id=user_id,
            device_id=device_id,
            event_type="warning_auto",
            severity="warning",
            status="created",
            title="Automatic Warning: Sustained Abnormal Vitals",
            description=f"Automatic, unconfirmed. Vitals exceeded configurable safety thresholds for >=30s: {candidate['reason']}",
            lat=candidate.get("lat"),
            lng=candidate.get("lng"),
            map_url=f"https://www.google.com/maps?q={candidate.get('lat')},{candidate.get('lng')}" if candidate.get("lat") and candidate.get("lng") else None,
            ack_token=uuid.uuid4().hex,
            vitals_snapshot=json.dumps({
                "bpm": candidate.get("bpm"),
                "spo2": candidate.get("spo2"),
                "temp_c": candidate.get("temp_c"),
                "reason": candidate.get("reason"),
                "sustained_duration": candidate.get("duration_secs")
            })
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        # Dispatch notifications
        dispatch_emergency_notifications(db, event)

        # Broadcast confirmed event to UI
        await broadcast_event("event_created", {
            "id": event.id,
            "title": event.title,
            "status": event.status,
            "severity": event.severity,
            "event_type": event.event_type
        })
    finally:
        tracker["pending_candidate"] = None
        db.close()


def cancel_pending_candidate(device_id: str, candidate_id: str) -> bool:
    """Cancels a pending auto-warning candidate during the 15-second grace countdown."""
    tracker = _DEVICE_TRACKERS.get(device_id)
    if not tracker:
        # Search all trackers
        for dev, trk in _DEVICE_TRACKERS.items():
            cand = trk.get("pending_candidate")
            if cand and cand.get("candidate_id") == candidate_id:
                trk["pending_candidate"] = {"status": "cancelled"}
                return True
        return False

    cand = tracker.get("pending_candidate")
    if cand and cand.get("candidate_id") == candidate_id:
        tracker["pending_candidate"] = {"status": "cancelled"}
        return True
    return False
