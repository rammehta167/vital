from datetime import datetime, timezone, timedelta
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from ..models import Reading, RawReading, Device, User
from ..schemas import (
    ReadingCreate, BulkReadingCreate, ReadingResponse, LatestReadingResponse,
    ReadingsHistoryResponse, ReadingsHistoryStats, MessageResponse
)
from ..security import verify_device_key, get_optional_current_user, get_current_user
from ..services.warning_engine import evaluate_reading_for_warning
from ..routers.stream import broadcast_event

router = APIRouter(prefix="/api/v1/readings", tags=["IoT Readings Ingestion & Analytics"])


@router.post("", response_model=ReadingResponse)
async def ingest_reading(
    reading_in: ReadingCreate,
    request: Request,
    db: Session = Depends(get_db),
    device_key: str = Depends(verify_device_key)
):
    now = datetime.now(timezone.utc)
    raw_body = await request.body()

    # 1. Store Raw Reading
    raw_entry = RawReading(
        device_id=reading_in.device_id,
        raw_payload=raw_body.decode("utf-8", errors="replace"),
        ip_address=request.client.host if request.client else None,
        received_at=now
    )
    db.add(raw_entry)

    # 2. Update Device Status & get User mapping
    device = db.query(Device).filter(Device.device_id == reading_in.device_id).first()
    user_id = None
    if not device:
        # Auto-register device
        # Check if default patient exists
        default_patient = db.query(User).filter(User.role == "patient").first()
        user_id = default_patient.id if default_patient else None
        device = Device(
            device_id=reading_in.device_id,
            user_id=user_id,
            name="Simulated ESP32 Vital Tracker",
            status="online",
            last_seen=now
        )
        db.add(device)
    else:
        device.status = "online"
        device.last_seen = now
        user_id = device.user_id

    # 3. Determine validity based on signal quality
    is_valid = True
    sig_quality = (reading_in.signal_quality or "good").lower()
    bpm_val = reading_in.bpm
    spo2_val = reading_in.spo2
    temp_val = reading_in.temp_c

    if sig_quality == "no_finger":
        is_valid = False
        bpm_val = None
        spo2_val = None
    elif sig_quality in ("poor", "noisy"):
        is_valid = False  # Not clinically reliable

    measured_at = reading_in.ts or now
    if measured_at.tzinfo is None:
        measured_at = measured_at.replace(tzinfo=timezone.utc)

    # 4. Normalized Reading Entry
    ecg_json = json.dumps(reading_in.ecg_sample) if reading_in.ecg_sample else None

    norm_entry = Reading(
        device_id=reading_in.device_id,
        user_id=user_id,
        bpm=bpm_val,
        spo2=spo2_val,
        temp_c=temp_val,
        ecg_sample=ecg_json,
        lat=reading_in.lat,
        lng=reading_in.lng,
        signal_quality=sig_quality,
        is_valid=is_valid,
        measured_at=measured_at,
        received_at=now
    )
    db.add(norm_entry)
    db.commit()
    db.refresh(norm_entry)

    # 5. Check Automatic Warning criteria
    await evaluate_reading_for_warning(db, norm_entry, user_id=user_id)

    # 6. Broadcast SSE live update
    await broadcast_event("reading_received", {
        "id": norm_entry.id,
        "device_id": norm_entry.device_id,
        "bpm": norm_entry.bpm,
        "spo2": norm_entry.spo2,
        "temp_c": norm_entry.temp_c,
        "signal_quality": norm_entry.signal_quality,
        "is_valid": norm_entry.is_valid,
        "lat": norm_entry.lat,
        "lng": norm_entry.lng,
        "measured_at": norm_entry.measured_at.isoformat(),
        "received_at": norm_entry.received_at.isoformat()
    })

    return norm_entry


@router.post("/bulk", response_model=MessageResponse)
async def ingest_bulk_readings(
    bulk_in: BulkReadingCreate,
    request: Request,
    db: Session = Depends(get_db),
    device_key: str = Depends(verify_device_key)
):
    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.device_id == bulk_in.device_id).first()
    user_id = device.user_id if device else None

    if device:
        device.status = "online"
        device.last_seen = now

    created_count = 0
    for item in bulk_in.readings:
        sig_quality = (item.signal_quality or "good").lower()
        is_valid = sig_quality == "good"
        bpm_val = None if sig_quality == "no_finger" else item.bpm
        spo2_val = None if sig_quality == "no_finger" else item.spo2

        ts = item.ts or now
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        entry = Reading(
            device_id=bulk_in.device_id,
            user_id=user_id,
            bpm=bpm_val,
            spo2=spo2_val,
            temp_c=item.temp_c,
            lat=item.lat,
            lng=item.lng,
            signal_quality=sig_quality,
            is_valid=is_valid,
            measured_at=ts,
            received_at=now
        )
        db.add(entry)
        created_count += 1

    db.commit()
    return {"message": f"Successfully processed {created_count} buffered readings.", "detail": f"Device {bulk_in.device_id}"}


@router.get("/latest", response_model=LatestReadingResponse)
def get_latest_reading(
    device_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    query = db.query(Reading)
    if device_id:
        query = query.filter(Reading.device_id == device_id)
    latest = query.order_by(Reading.id.desc()).first()

    if not latest:
        return {
            "reading": None,
            "is_stale": True,
            "device_status": "offline",
            "message": "No sensor readings recorded yet."
        }

    # Stale calculation: if last received reading is > 10 seconds old
    received_at = latest.received_at
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=timezone.utc)

    diff_seconds = (now - received_at).total_seconds()
    is_stale = diff_seconds > 10.0
    device_status = "offline" if diff_seconds > 30.0 else ("degraded" if is_stale else "online")

    return {
        "reading": latest,
        "is_stale": is_stale,
        "device_status": device_status,
        "message": "simulated estimate (Not a certified medical device)"
    }


@router.get("/history", response_model=ReadingsHistoryResponse)
def get_readings_history(
    range: str = "day",  # day, week, dense
    device_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    query = db.query(Reading)

    if device_id:
        query = query.filter(Reading.device_id == device_id)

    if range == "week":
        start_time = now - timedelta(days=7)
        query = query.filter(Reading.measured_at >= start_time)
        range_label = "Past 7 Days"
    elif range == "dense":
        start_time = now - timedelta(hours=1)
        query = query.filter(Reading.measured_at >= start_time)
        range_label = "Last 60 Minutes (Dense)"
    else:  # day
        start_time = now - timedelta(hours=24)
        query = query.filter(Reading.measured_at >= start_time)
        range_label = "Past 24 Hours"

    readings = query.order_by(Reading.id.desc()).limit(limit).all()
    # Reverse so chronological for charts
    readings_chronological = list(reversed(readings))

    # Calculate statistics on valid readings
    valid_readings = [r for r in readings if r.is_valid and r.bpm is not None and r.spo2 is not None]
    if valid_readings:
        bpms = [r.bpm for r in valid_readings if r.bpm]
        spo2s = [r.spo2 for r in valid_readings if r.spo2]
        temps = [r.temp_c for r in valid_readings if r.temp_c]

        stats = ReadingsHistoryStats(
            min_bpm=min(bpms) if bpms else None,
            avg_bpm=round(sum(bpms) / len(bpms), 1) if bpms else None,
            max_bpm=max(bpms) if bpms else None,
            min_spo2=min(spo2s) if spo2s else None,
            avg_spo2=round(sum(spo2s) / len(spo2s), 1) if spo2s else None,
            max_spo2=max(spo2s) if spo2s else None,
            min_temp=min(temps) if temps else None,
            avg_temp=round(sum(temps) / len(temps), 1) if temps else None,
            max_temp=max(temps) if temps else None,
            total_samples=len(readings)
        )
    else:
        stats = ReadingsHistoryStats(total_samples=len(readings))

    return {
        "stats": stats,
        "readings": readings_chronological,
        "range_label": range_label
    }
