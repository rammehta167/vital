from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.orm import relationship
from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="patient", nullable=False)  # patient, caregiver, responder, doctor, admin
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)  # e.g., B+, O-
    allergies = Column(Text, default="", nullable=True)  # e.g., Penicillin
    chronic_conditions = Column(Text, default="", nullable=True)  # e.g., Hypertension
    phone = Column(String(50), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    readings = relationship("Reading", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    symptoms = relationship("SymptomSession", back_populates="user", cascade="all, delete-orphan")
    summaries = relationship("DoctorSummary", back_populates="user", cascade="all, delete-orphan")
    emergency_tokens = relationship("EmergencyToken", back_populates="user", cascade="all, delete-orphan")
    consent = relationship("Consent", uselist=False, back_populates="user", cascade="all, delete-orphan")


class Consent(Base):
    __tablename__ = "consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    telemetry_collection = Column(Boolean, default=True)
    location_tracking = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    ai_assistance = Column(Boolean, default=True)
    accepted_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="consent")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(100), default="Pulse & Oximeter Sensor Unit")
    api_key_hash = Column(String(255), nullable=True)
    status = Column(String(50), default="offline")  # online, offline, degraded
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="devices")
    readings = relationship("Reading", back_populates="device", cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.device_id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    bpm = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temp_c = Column(Float, nullable=True)
    ecg_sample = Column(Text, nullable=True)  # JSON-encoded array of waveform samples
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    signal_quality = Column(String(50), default="good")  # good, noisy, poor, no_finger
    is_valid = Column(Boolean, default=True)
    measured_at = Column(DateTime, index=True, nullable=False)
    received_at = Column(DateTime, default=utcnow, index=True)

    device = relationship("Device", back_populates="readings")
    user = relationship("User", back_populates="readings")


class RawReading(Base):
    __tablename__ = "raw_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False)
    raw_payload = Column(Text, nullable=False)
    ip_address = Column(String(100), nullable=True)
    received_at = Column(DateTime, default=utcnow)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    device_id = Column(String(100), nullable=True)
    event_type = Column(String(50), nullable=False)  # sos_manual, warning_auto, fall_detected, system
    severity = Column(String(50), default="critical")  # critical, warning, info
    status = Column(String(50), default="created")  # created, sent, delivered, acknowledged, resolved, failed
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    map_url = Column(String(500), nullable=True)
    vitals_snapshot = Column(Text, nullable=True)  # JSON-encoded 60-second vitals list
    ack_token = Column(String(255), unique=True, index=True, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    user = relationship("User", back_populates="events")
    logs = relationship("EventLog", back_populates="event", cascade="all, delete-orphan")


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    channel = Column(String(50), nullable=False)  # in_app, telegram, sms_simulated, email_simulated
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    event = relationship("Event", back_populates="logs")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    relationship_type = Column(String(100), default="Family")  # Family, Doctor, Neighbor, Caregiver
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    notify_sos = Column(Boolean, default=True)
    notify_warning = Column(Boolean, default=True)
    priority_order = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="contacts")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    strength = Column(String(100), nullable=True)  # e.g., 5mg, 500mg
    form = Column(String(100), default="Tablet")  # Tablet, Capsule, Syrup, Injection
    times_per_day = Column(Integer, default=1)
    schedule_times = Column(Text, default="[\"08:00\"]")  # JSON array string
    duration_days = Column(Integer, default=30)
    instructions = Column(Text, default="After meals")
    confidence_score = Column(Float, default=1.0)  # OCR extraction confidence
    is_verified = Column(Boolean, default=True)  # Requires user confirmation if from scan
    raw_ocr_extracted = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="medications")
    adherence_logs = relationship("AdherenceLog", back_populates="medication", cascade="all, delete-orphan")


class AdherenceLog(Base):
    __tablename__ = "adherence_logs"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    scheduled_time = Column(DateTime, nullable=False)
    action = Column(String(50), nullable=False)  # taken, snoozed, skipped
    action_time = Column(DateTime, default=utcnow)
    notes = Column(Text, nullable=True)

    medication = relationship("Medication", back_populates="adherence_logs")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, image/jpeg, image/png
    uploaded_at = Column(DateTime, default=utcnow)
    extracted_data = Column(Text, default="[]")  # JSON array of extracted test records
    summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="reports")


class SymptomSession(Base):
    __tablename__ = "symptom_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    language = Column(String(20), default="en")  # en, hi, hinglish
    input_text = Column(Text, nullable=False)
    speech_transcript = Column(Text, nullable=True)
    rules_version = Column(String(50), default="triage_rules_v1.0.0")
    red_flags_detected = Column(Text, default="[]")  # JSON array of detected red flags
    outcome = Column(String(50), nullable=False)  # emergency, prompt_care, routine_consult, self_care_info
    guidance = Column(Text, nullable=False)
    follow_up_questions = Column(Text, default="[]")  # JSON array of follow-up questions
    ai_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="symptoms")


class DoctorSummary(Base):
    __tablename__ = "doctor_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="Structured Clinical Summary")
    structured_content = Column(Text, nullable=False)  # JSON structured sections with provenance
    share_token = Column(String(255), unique=True, index=True, nullable=True)
    share_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="summaries")


class EmergencyToken(Base):
    __tablename__ = "emergency_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    visible_fields = Column(Text, default="[\"blood_group\", \"allergies\", \"chronic_conditions\", \"emergency_contacts\"]")
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="emergency_tokens")
    access_logs = relationship("EmergencyAccessLog", back_populates="token_rel", cascade="all, delete-orphan")


class EmergencyAccessLog(Base):
    __tablename__ = "emergency_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    emergency_token_id = Column(Integer, ForeignKey("emergency_tokens.id"), nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    accessed_at = Column(DateTime, default=utcnow)

    token_rel = relationship("EmergencyToken", back_populates="access_logs")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., AUTH_LOGIN, READ_DATA, EMERGENCY_VIEW
    resource = Column(String(150), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)
