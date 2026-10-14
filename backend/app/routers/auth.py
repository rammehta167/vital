from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Consent, Reading, Event, Contact, Medication, Report, SymptomSession, DoctorSummary, EmergencyToken
from ..schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse, DemoLoginRequest,
    ConsentUpdate, ConsentResponse, MessageResponse
)
from ..security import (
    hash_password, verify_password, create_access_token, get_current_user
)
from ..services.audit import log_audit

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Privacy"])


@router.post("/register", response_model=TokenResponse)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or "patient",
        age=user_in.age,
        gender=user_in.gender,
        blood_group=user_in.blood_group,
        allergies=user_in.allergies or "",
        chronic_conditions=user_in.chronic_conditions or "",
        phone=user_in.phone,
        emergency_contact=user_in.emergency_contact
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize consent record
    consent = Consent(user_id=user.id)
    db.add(consent)
    db.commit()

    log_audit(db, "REGISTER", "User", f"Registered new user {user.email}", user_id=user.id, actor_role=user.role, ip_address=request.client.host if request.client else None)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    log_audit(db, "LOGIN", "User", f"User {user.email} logged in", user_id=user.id, actor_role=user.role, ip_address=request.client.host if request.client else None)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/demo-login", response_model=TokenResponse)
def demo_login(demo_in: DemoLoginRequest, request: Request, db: Session = Depends(get_db)):
    target_role = demo_in.role.lower()
    user = db.query(User).filter(User.role == target_role).first()
    if not user:
        # Fallback to any user or create a temporary demo user
        user = User(
            email=f"demo_{target_role}@example.com",
            hashed_password=hash_password("DemoPassword123!"),
            full_name=f"Demo {target_role.capitalize()}",
            role=target_role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        consent = Consent(user_id=user.id)
        db.add(consent)
        db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role})
    log_audit(db, "DEMO_LOGIN", "User", f"Demo login as {target_role}", user_id=user.id, actor_role=user.role, ip_address=request.client.host if request.client else None)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(
    update_data: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_fields = ["full_name", "age", "gender", "blood_group", "allergies", "chronic_conditions", "phone", "emergency_contact"]
    for field in allowed_fields:
        if field in update_data:
            setattr(current_user, field, update_data[field])

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    log_audit(db, "UPDATE_PROFILE", "User", "Updated profile settings", user_id=current_user.id, actor_role=current_user.role, ip_address=request.client.host if request.client else None)
    return current_user


@router.get("/consent", response_model=ConsentResponse)
def get_consent(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
    if not consent:
        consent = Consent(user_id=current_user.id)
        db.add(consent)
        db.commit()
        db.refresh(consent)
    return consent


@router.put("/consent", response_model=ConsentResponse)
def update_consent(
    consent_in: ConsentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()
    if not consent:
        consent = Consent(user_id=current_user.id)
        db.add(consent)

    consent.telemetry_collection = consent_in.telemetry_collection
    consent.location_tracking = consent_in.location_tracking
    consent.notifications_enabled = consent_in.notifications_enabled
    consent.ai_assistance = consent_in.ai_assistance
    consent.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(consent)

    log_audit(db, "CONSENT_UPDATE", "Consent", f"Updated consents: {consent_in.dict()}", user_id=current_user.id, actor_role=current_user.role, ip_address=request.client.host if request.client else None)
    return consent


@router.get("/export-my-data")
def export_my_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log_audit(db, "DATA_EXPORT", "User", "Exported full personal record", user_id=current_user.id, actor_role=current_user.role, ip_address=request.client.host if request.client else None)

    readings = db.query(Reading).filter(Reading.user_id == current_user.id).all()
    events = db.query(Event).filter(Event.user_id == current_user.id).all()
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).all()
    medications = db.query(Medication).filter(Medication.user_id == current_user.id).all()
    reports = db.query(Report).filter(Report.user_id == current_user.id).all()
    symptoms = db.query(SymptomSession).filter(SymptomSession.user_id == current_user.id).all()
    consent = db.query(Consent).filter(Consent.user_id == current_user.id).first()

    return {
        "export_metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "notice": "Exported patient data package. Educational prototype.",
        },
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "age": current_user.age,
            "gender": current_user.gender,
            "blood_group": current_user.blood_group,
            "allergies": current_user.allergies,
            "chronic_conditions": current_user.chronic_conditions,
            "phone": current_user.phone
        },
        "consent": {
            "telemetry_collection": consent.telemetry_collection if consent else True,
            "location_tracking": consent.location_tracking if consent else True,
            "notifications_enabled": consent.notifications_enabled if consent else True,
            "ai_assistance": consent.ai_assistance if consent else True,
        },
        "contacts": [
            {"name": c.name, "relationship": c.relationship_type, "phone": c.phone, "email": c.email} for c in contacts
        ],
        "medications": [
            {"name": m.name, "strength": m.strength, "form": m.form, "schedule": m.schedule_times} for m in medications
        ],
        "vitals_samples_count": len(readings),
        "recent_readings": [
            {"bpm": r.bpm, "spo2": r.spo2, "temp_c": r.temp_c, "signal_quality": r.signal_quality, "measured_at": r.measured_at.isoformat()}
            for r in readings[-50:]
        ],
        "events_count": len(events),
        "reports_count": len(reports),
        "symptoms_count": len(symptoms)
    }


@router.delete("/delete-my-data", response_model=MessageResponse)
def delete_my_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    uid = current_user.id
    log_audit(db, "DELETE_DATA", "User", "Patient requested full account and data purge", user_id=uid, actor_role=current_user.role, ip_address=request.client.host if request.client else None)

    # Cascading deletion via ORM
    db.query(Reading).filter(Reading.user_id == uid).delete()
    db.query(Event).filter(Event.user_id == uid).delete()
    db.query(Contact).filter(Contact.user_id == uid).delete()
    db.query(Medication).filter(Medication.user_id == uid).delete()
    db.query(Report).filter(Report.user_id == uid).delete()
    db.query(SymptomSession).filter(SymptomSession.user_id == uid).delete()
    db.query(DoctorSummary).filter(DoctorSummary.user_id == uid).delete()
    db.query(EmergencyToken).filter(EmergencyToken.user_id == uid).delete()
    db.query(Consent).filter(Consent.user_id == uid).delete()

    db.delete(current_user)
    db.commit()

    return {"message": "All personal data, readings, medications, and account records have been permanently deleted."}
