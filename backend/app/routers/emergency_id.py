import io
import base64
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import EmergencyToken, EmergencyAccessLog, User, Contact, Medication, Reading
from ..schemas import EmergencyTokenCreate, EmergencyTokenResponse, PublicEmergencyView, MessageResponse
from ..security import get_current_user
from ..services.audit import log_audit

router = APIRouter(prefix="/api/v1/emergency-id", tags=["Emergency Medical ID & QR"])


@router.post("/generate", response_model=EmergencyTokenResponse)
def generate_emergency_qr(
    token_in: EmergencyTokenCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    # Revoke any previous active tokens for this user
    db.query(EmergencyToken).filter(EmergencyToken.user_id == current_user.id, EmergencyToken.is_revoked == False).update({"is_revoked": True})

    token_str = uuid.uuid4().hex
    expires_at = now + timedelta(hours=token_in.expire_hours)

    token_rec = EmergencyToken(
        user_id=current_user.id,
        token=token_str,
        visible_fields=json.dumps(token_in.visible_fields),
        expires_at=expires_at,
        is_revoked=False,
        created_at=now
    )
    db.add(token_rec)
    db.commit()
    db.refresh(token_rec)

    # Base URL for public scan
    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/emergency/{token_str}"

    # Generate QR Code image as base64 PNG
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2
    )
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    log_audit(db, "GENERATE_EMERGENCY_QR", "EmergencyToken", f"Generated token valid for {token_in.expire_hours}h", user_id=current_user.id)

    return {
        "id": token_rec.id,
        "token": token_str,
        "public_url": public_url,
        "qr_code_base64": f"data:image/png;base64,{qr_b64}",
        "visible_fields": token_in.visible_fields,
        "expires_at": expires_at,
        "is_revoked": False,
        "created_at": now
    }


@router.get("/active", response_model=Optional[EmergencyTokenResponse])
def get_active_emergency_qr(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    token_rec = (
        db.query(EmergencyToken)
        .filter(EmergencyToken.user_id == current_user.id, EmergencyToken.is_revoked == False, EmergencyToken.expires_at > now)
        .order_by(EmergencyToken.id.desc())
        .first()
    )
    if not token_rec:
        return None

    base_url = str(request.base_url).rstrip("/")
    public_url = f"{base_url}/emergency/{token_rec.token}"

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "id": token_rec.id,
        "token": token_rec.token,
        "public_url": public_url,
        "qr_code_base64": f"data:image/png;base64,{qr_b64}",
        "visible_fields": json.loads(token_rec.visible_fields),
        "expires_at": token_rec.expires_at,
        "is_revoked": token_rec.is_revoked,
        "created_at": token_rec.created_at
    }


@router.post("/revoke", response_model=MessageResponse)
def revoke_emergency_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(EmergencyToken).filter(EmergencyToken.user_id == current_user.id, EmergencyToken.is_revoked == False).update({"is_revoked": True})
    db.commit()
    log_audit(db, "REVOKE_EMERGENCY_QR", "EmergencyToken", "Revoked all active emergency tokens", user_id=current_user.id)
    return {"message": "Emergency ID QR code successfully revoked and deactivated."}


@router.get("/access-logs")
def get_access_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tokens = db.query(EmergencyToken).filter(EmergencyToken.user_id == current_user.id).all()
    token_ids = [t.id for t in tokens]
    logs = (
        db.query(EmergencyAccessLog)
        .filter(EmergencyAccessLog.emergency_token_id.in_(token_ids))
        .order_by(EmergencyAccessLog.id.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": l.id,
            "token_id": l.emergency_token_id,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "accessed_at": l.accessed_at.isoformat()
        } for l in logs
    ]


@router.get("/public/{token}", response_model=PublicEmergencyView)
def view_public_emergency_card(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    token_rec = db.query(EmergencyToken).filter(EmergencyToken.token == token).first()

    if not token_rec or token_rec.is_revoked or token_rec.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Emergency Medical ID token is invalid, expired, or has been revoked by the patient."
        )

    # Record Access Log
    access_log = EmergencyAccessLog(
        emergency_token_id=token_rec.id,
        ip_address=request.client.host if request.client else "Unknown",
        user_agent=request.headers.get("user-agent", "Unknown"),
        accessed_at=now
    )
    db.add(access_log)
    db.commit()

    log_audit(db, "EMERGENCY_QR_SCANNED", "EmergencyToken", f"Token {token[:8]} scanned by first responder", user_id=token_rec.user_id, ip_address=request.client.host if request.client else None)

    patient = db.query(User).filter(User.id == token_rec.user_id).first()
    visible_fields = json.loads(token_rec.visible_fields) if token_rec.visible_fields else []

    # Optional fields
    blood_group = patient.blood_group if "blood_group" in visible_fields else None
    allergies = patient.allergies if "allergies" in visible_fields else None
    chronic_conditions = patient.chronic_conditions if "chronic_conditions" in visible_fields else None

    # Medications
    meds_out = []
    if "medications" in visible_fields or "medicines" in visible_fields:
        meds = db.query(Medication).filter(Medication.user_id == patient.id).all()
        meds_out = [{"name": m.name, "strength": m.strength, "instructions": m.instructions} for m in meds]

    # Contacts
    contacts_out = []
    if "emergency_contacts" in visible_fields or "contacts" in visible_fields:
        contacts = db.query(Contact).filter(Contact.user_id == patient.id).order_by(Contact.priority_order).all()
        contacts_out = [{"name": c.name, "relationship": c.relationship_type, "phone": c.phone} for c in contacts]

    # Latest reading
    latest_reading = db.query(Reading).filter(Reading.user_id == patient.id).order_by(Reading.id.desc()).first()
    vitals_dict = None
    if latest_reading:
        vitals_dict = {
            "bpm": latest_reading.bpm,
            "spo2": latest_reading.spo2,
            "temp_c": latest_reading.temp_c,
            "signal_quality": latest_reading.signal_quality,
            "measured_at": latest_reading.measured_at.isoformat()
        }

    return {
        "is_valid": True,
        "patient_name": patient.full_name,
        "age": patient.age,
        "gender": patient.gender,
        "blood_group": blood_group,
        "allergies": allergies,
        "chronic_conditions": chronic_conditions,
        "current_medications": meds_out,
        "emergency_contacts": contacts_out,
        "latest_simulated_vitals": vitals_dict,
        "disclaimer": "Authorised first responder view. Educational prototype. Not a certified clinical device.",
        "expires_at": token_rec.expires_at
    }
