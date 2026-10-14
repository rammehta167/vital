import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Reading, Event, Medication, Report, SymptomSession, DoctorSummary
from ..schemas import DoctorSummaryResponse, MessageResponse
from ..security import get_current_user, get_optional_current_user
from ..services.ai_client import build_structured_doctor_summary

router = APIRouter(prefix="/api/v1/summary", tags=["AI Doctor Clinical Summary"])


@router.post("/generate", response_model=DoctorSummaryResponse)
def generate_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # 1. Fetch patient details
    patient_info = {
        "full_name": current_user.full_name,
        "age": current_user.age,
        "gender": current_user.gender,
        "blood_group": current_user.blood_group,
        "allergies": current_user.allergies,
        "chronic_conditions": current_user.chronic_conditions
    }

    # 2. Fetch vitals stats & readings
    readings = (
        db.query(Reading)
        .filter(Reading.user_id == current_user.id, Reading.measured_at >= seven_days_ago)
        .order_by(Reading.id.desc())
        .all()
    )
    valid_readings = [r for r in readings if r.is_valid and r.bpm is not None]
    bpms = [r.bpm for r in valid_readings if r.bpm]
    spo2s = [r.spo2 for r in valid_readings if r.spo2]
    temps = [r.temp_c for r in valid_readings if r.temp_c]

    vitals_stats = {
        "min_bpm": min(bpms) if bpms else None,
        "avg_bpm": round(sum(bpms)/len(bpms), 1) if bpms else None,
        "max_bpm": max(bpms) if bpms else None,
        "min_spo2": min(spo2s) if spo2s else None,
        "avg_spo2": round(sum(spo2s)/len(spo2s), 1) if spo2s else None,
        "max_spo2": max(spo2s) if spo2s else None,
        "min_temp": min(temps) if temps else None,
        "avg_temp": round(sum(temps)/len(temps), 1) if temps else None,
        "max_temp": max(temps) if temps else None,
        "total_samples": len(readings)
    }

    recent_readings_data = [
        {"bpm": r.bpm, "spo2": r.spo2, "temp_c": r.temp_c, "measured_at": r.measured_at.isoformat()}
        for r in readings[:10]
    ]

    # 3. Medications
    meds = db.query(Medication).filter(Medication.user_id == current_user.id).all()
    meds_data = [
        {
            "name": m.name,
            "strength": m.strength,
            "form": m.form,
            "schedule_times": m.schedule_times,
            "is_verified": m.is_verified
        } for m in meds
    ]

    # 4. Reports
    reports = db.query(Report).filter(Report.user_id == current_user.id).all()
    reports_data = [
        {
            "filename": r.filename,
            "extracted_data": json.loads(r.extracted_data) if r.extracted_data else []
        } for r in reports
    ]

    # 5. Symptoms
    symptoms = db.query(SymptomSession).filter(SymptomSession.user_id == current_user.id).all()
    symptoms_data = [
        {
            "input_text": s.input_text,
            "outcome": s.outcome,
            "red_flags_detected": json.loads(s.red_flags_detected) if s.red_flags_detected else [],
            "created_at": s.created_at.isoformat()
        } for s in symptoms
    ]

    # 6. Events
    events = db.query(Event).filter(Event.user_id == current_user.id).all()
    events_data = [
        {
            "title": e.title,
            "event_type": e.event_type,
            "severity": e.severity,
            "status": e.status,
            "created_at": e.created_at.isoformat()
        } for e in events
    ]

    structured_summary = build_structured_doctor_summary(
        patient_info=patient_info,
        vitals_stats=vitals_stats,
        recent_readings=recent_readings_data,
        medications=meds_data,
        reports=reports_data,
        symptoms=symptoms_data,
        events=events_data
    )

    share_token = uuid.uuid4().hex
    share_expires_at = now + timedelta(days=3)  # 72 hours doctor share link

    doc_sum = DoctorSummary(
        user_id=current_user.id,
        title=f"Clinical Summary for {current_user.full_name} ({now.strftime('%d %b %Y')})",
        structured_content=json.dumps(structured_summary),
        share_token=share_token,
        share_expires_at=share_expires_at,
        created_at=now
    )
    db.add(doc_sum)
    db.commit()
    db.refresh(doc_sum)

    return {
        "id": doc_sum.id,
        "user_id": doc_sum.user_id,
        "title": doc_sum.title,
        "structured_content": structured_summary,
        "share_token": doc_sum.share_token,
        "share_expires_at": doc_sum.share_expires_at,
        "created_at": doc_sum.created_at
    }


@router.get("/latest", response_model=DoctorSummaryResponse)
def get_latest_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc_sum = db.query(DoctorSummary).filter(DoctorSummary.user_id == current_user.id).order_by(DoctorSummary.id.desc()).first()
    if not doc_sum:
        # Generate automatically if none exists yet
        return generate_summary(current_user=current_user, db=db)

    return {
        "id": doc_sum.id,
        "user_id": doc_sum.user_id,
        "title": doc_sum.title,
        "structured_content": json.loads(doc_sum.structured_content),
        "share_token": doc_sum.share_token,
        "share_expires_at": doc_sum.share_expires_at,
        "created_at": doc_sum.created_at
    }


@router.get("/share/{share_token}")
def view_shared_doctor_summary(
    share_token: str,
    db: Session = Depends(get_db)
):
    doc_sum = db.query(DoctorSummary).filter(DoctorSummary.share_token == share_token).first()
    if not doc_sum:
        raise HTTPException(status_code=404, detail="Shared summary link not found or expired.")

    now = datetime.now(timezone.utc)
    if doc_sum.share_expires_at and doc_sum.share_expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=410, detail="This doctor summary share link has expired.")

    return {
        "title": doc_sum.title,
        "structured_content": json.loads(doc_sum.structured_content),
        "created_at": doc_sum.created_at,
        "expires_at": doc_sum.share_expires_at,
        "is_active": True,
        "disclaimer": "Confidential patient clinical summary. Educational prototype."
    }
