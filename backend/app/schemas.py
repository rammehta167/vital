from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# --- Base Response ---
class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


# --- Auth & User ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "patient"
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class DemoLoginRequest(BaseModel):
    role: str = "patient"  # patient, caregiver, responder, doctor, admin


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ConsentUpdate(BaseModel):
    telemetry_collection: bool = True
    location_tracking: bool = True
    notifications_enabled: bool = True
    ai_assistance: bool = True


class ConsentResponse(ConsentUpdate):
    id: int
    user_id: int
    accepted_at: datetime

    class Config:
        from_attributes = True


# --- IoT Device & Readings ---
class ReadingCreate(BaseModel):
    device_id: str
    bpm: Optional[float] = None
    spo2: Optional[float] = None
    temp_c: Optional[float] = None
    ecg_sample: Optional[List[float]] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    signal_quality: str = "good"  # good, noisy, poor, no_finger
    ts: Optional[datetime] = None


class BulkReadingCreate(BaseModel):
    device_id: str
    readings: List[ReadingCreate]


class ReadingResponse(BaseModel):
    id: int
    device_id: str
    user_id: Optional[int] = None
    bpm: Optional[float] = None
    spo2: Optional[float] = None
    temp_c: Optional[float] = None
    ecg_sample: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    signal_quality: str
    is_valid: bool
    measured_at: datetime
    received_at: datetime

    class Config:
        from_attributes = True


class LatestReadingResponse(BaseModel):
    reading: Optional[ReadingResponse] = None
    is_stale: bool = False
    device_status: str = "offline"
    message: str = "simulated estimate"


class ReadingsHistoryStats(BaseModel):
    min_bpm: Optional[float] = None
    avg_bpm: Optional[float] = None
    max_bpm: Optional[float] = None
    min_spo2: Optional[float] = None
    avg_spo2: Optional[float] = None
    max_spo2: Optional[float] = None
    min_temp: Optional[float] = None
    avg_temp: Optional[float] = None
    max_temp: Optional[float] = None
    total_samples: int = 0


class ReadingsHistoryResponse(BaseModel):
    stats: ReadingsHistoryStats
    readings: List[ReadingResponse]
    range_label: str


# --- Events & SOS ---
class SOSRequest(BaseModel):
    device_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    idempotency_key: Optional[str] = None
    details: Optional[str] = "Manual SOS button activated by patient"


class EventLogResponse(BaseModel):
    id: int
    status: str
    channel: str
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    device_id: Optional[str] = None
    event_type: str
    severity: str
    status: str  # created, sent, delivered, acknowledged, resolved, failed
    title: str
    description: Optional[str] = None
    idempotency_key: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    map_url: Optional[str] = None
    vitals_snapshot: Optional[str] = None
    ack_token: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    created_at: datetime
    logs: List[EventLogResponse] = []

    class Config:
        from_attributes = True


class EventResolveRequest(BaseModel):
    resolved_by: Optional[str] = "User"
    notes: Optional[str] = None


# --- Contacts ---
class ContactCreate(BaseModel):
    name: str
    relationship_type: str = "Family"
    phone: str
    email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None
    notify_sos: bool = True
    notify_warning: bool = True
    priority_order: int = 1


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    relationship_type: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None
    notify_sos: Optional[bool] = None
    notify_warning: Optional[bool] = None
    priority_order: Optional[int] = None


class ContactResponse(ContactCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Devices ---
class DeviceCreate(BaseModel):
    device_id: str
    name: str = "Pulse & Oximeter Sensor Unit"


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    user_id: Optional[int] = None
    name: str
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Medications ---
class MedicationCreate(BaseModel):
    name: str
    strength: Optional[str] = None
    form: str = "Tablet"
    times_per_day: int = 1
    schedule_times: List[str] = ["08:00"]
    duration_days: int = 30
    instructions: str = "After meals"
    is_verified: bool = True


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    times_per_day: Optional[int] = None
    schedule_times: Optional[List[str]] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None
    is_verified: Optional[bool] = None


class AdherenceLogCreate(BaseModel):
    medication_id: int
    scheduled_time: datetime
    action: str  # taken, snoozed, skipped
    notes: Optional[str] = None


class AdherenceLogResponse(BaseModel):
    id: int
    medication_id: int
    user_id: int
    scheduled_time: datetime
    action: str
    action_time: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MedicationResponse(BaseModel):
    id: int
    user_id: int
    name: str
    strength: Optional[str] = None
    form: str
    times_per_day: int
    schedule_times: str  # JSON string
    duration_days: int
    instructions: str
    confidence_score: float
    is_verified: bool
    created_at: datetime
    adherence_logs: List[AdherenceLogResponse] = []

    class Config:
        from_attributes = True


class MedicationScanResponse(BaseModel):
    name: str
    strength: Optional[str] = None
    form: str
    confidence: float
    suggested_instructions: str
    requires_verification: bool = True
    disclaimer: str = "Always verify extracted details before confirming prescription schedule."


# --- Reports ---
class ReportFieldVerified(BaseModel):
    test_name: str
    value: str
    unit: str
    reference_range: str
    confidence: float
    status: str = "verified"  # verified, unverified


class ReportResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    uploaded_at: datetime
    extracted_data: str  # JSON
    summary: Optional[str] = None

    class Config:
        from_attributes = True


# --- Symptoms & Triage ---
class SymptomInput(BaseModel):
    input_text: str
    language: str = "en"
    speech_transcript: Optional[str] = None


class SymptomResponse(BaseModel):
    id: int
    language: str
    input_text: str
    rules_version: str
    red_flags_detected: List[str]
    outcome: str  # emergency, prompt_care, routine_consult, self_care_info
    guidance: str
    follow_up_questions: List[str]
    ai_explanation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Doctor Summary ---
class DoctorSummaryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    structured_content: Dict[str, Any]
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    created_at: datetime


# --- Emergency Medical ID ---
class EmergencyTokenCreate(BaseModel):
    visible_fields: List[str] = ["blood_group", "allergies", "chronic_conditions", "emergency_contacts"]
    expire_hours: int = 24


class EmergencyTokenResponse(BaseModel):
    id: int
    token: str
    public_url: str
    qr_code_base64: str
    visible_fields: List[str]
    expires_at: datetime
    is_revoked: bool
    created_at: datetime


class PublicEmergencyView(BaseModel):
    is_valid: bool
    patient_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    current_medications: List[Dict[str, Any]] = []
    emergency_contacts: List[Dict[str, Any]] = []
    latest_simulated_vitals: Optional[Dict[str, Any]] = None
    disclaimer: str
    expires_at: datetime


# --- AI Chat ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    is_emergency: bool = False
    disclaimer: str = "Educational advice only. Never diagnose or prescribe. In emergencies call 112."


# --- Simulator Control ---
class SimulatorControlRequest(BaseModel):
    action: str  # start, stop, switch_scenario, trigger_sos, trigger_fall
    scenario: Optional[str] = None  # normal_rest, exercise, fever, low_oxygen, high_pulse, no_finger, poor_signal, offline, network_fail
    device_id: Optional[str] = "ESP32-VITAL-01"


class SimulatorStatusResponse(BaseModel):
    is_running: bool
    current_scenario: str
    device_id: str
    buffered_count: int = 0
    target_url: str
    last_sent_at: Optional[datetime] = None


# --- Audit & System Health ---
class AuditEventResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    actor_role: Optional[str] = None
    action: str
    resource: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemHealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    ai_status: str  # "live" or "mock"
    ai_provider: str
    active_device_connected: bool
    simulator_active: bool
    database_connected: bool
    timestamp: datetime
