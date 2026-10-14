import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Medication, AdherenceLog, User
from ..schemas import (
    MedicationCreate, MedicationUpdate, MedicationResponse,
    AdherenceLogCreate, AdherenceLogResponse, MedicationScanResponse, MessageResponse
)
from ..security import get_current_user
from ..services.ai_client import mock_extract_medication

router = APIRouter(prefix="/api/v1/medications", tags=["Medications & Adherence"])


@router.get("", response_model=List[MedicationResponse])
def get_medications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meds = db.query(Medication).filter(Medication.user_id == current_user.id).all()
    return meds


@router.post("", response_model=MedicationResponse)
def add_medication(
    med_in: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    med = Medication(
        user_id=current_user.id,
        name=med_in.name,
        strength=med_in.strength,
        form=med_in.form,
        times_per_day=med_in.times_per_day,
        schedule_times=json.dumps(med_in.schedule_times),
        duration_days=med_in.duration_days,
        instructions=med_in.instructions,
        is_verified=med_in.is_verified,
        confidence_score=1.0 if med_in.is_verified else 0.85
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.post("/scan-strip", response_model=MedicationScanResponse)
async def scan_medicine_strip(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Simulates / performs AI vision OCR extraction of medicine packaging strip.
    Returns extracted name, strength, form, and confidence.
    User MUST review and confirm before saving.
    """
    extracted = mock_extract_medication(file.filename or "strip.jpg")
    return {
        "name": extracted["name"],
        "strength": extracted["strength"],
        "form": extracted["form"],
        "confidence": extracted["confidence"],
        "suggested_instructions": extracted["suggested_instructions"],
        "requires_verification": True,
        "disclaimer": "AI OCR extraction estimate. User must confirm fields before saving."
    }


@router.put("/{med_id}", response_model=MedicationResponse)
def update_medication(
    med_id: int,
    med_in: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    med = db.query(Medication).filter(Medication.id == med_id, Medication.user_id == current_user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    for field, val in med_in.dict(exclude_unset=True).items():
        if field == "schedule_times" and isinstance(val, list):
            med.schedule_times = json.dumps(val)
        else:
            setattr(med, field, val)

    db.commit()
    db.refresh(med)
    return med


@router.delete("/{med_id}", response_model=MessageResponse)
def delete_medication(
    med_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    med = db.query(Medication).filter(Medication.id == med_id, Medication.user_id == current_user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    db.delete(med)
    db.commit()
    return {"message": "Medication removed successfully"}


@router.post("/adherence", response_model=AdherenceLogResponse)
def log_adherence(
    log_in: AdherenceLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    med = db.query(Medication).filter(Medication.id == log_in.medication_id, Medication.user_id == current_user.id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    log_entry = AdherenceLog(
        medication_id=med.id,
        user_id=current_user.id,
        scheduled_time=log_in.scheduled_time,
        action=log_in.action.lower(),
        action_time=datetime.now(timezone.utc),
        notes=log_in.notes
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


@router.get("/adherence-summary")
def get_adherence_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    logs = (
        db.query(AdherenceLog)
        .filter(AdherenceLog.user_id == current_user.id, AdherenceLog.scheduled_time >= seven_days_ago)
        .all()
    )

    total_logs = len(logs)
    taken_count = sum(1 for l in logs if l.action == "taken")
    skipped_count = sum(1 for l in logs if l.action == "skipped")
    snoozed_count = sum(1 for l in logs if l.action == "snoozed")

    adherence_pct = round((taken_count / total_logs * 100), 1) if total_logs > 0 else 100.0

    return {
        "adherence_percentage": adherence_pct,
        "total_scheduled": total_logs,
        "taken": taken_count,
        "skipped": skipped_count,
        "snoozed": snoozed_count,
        "window": "Last 7 days"
    }
