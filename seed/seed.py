import os
import uuid
import json
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.app.db import SessionLocal, engine, Base
from backend.app.models import (
    User, Consent, Device, Reading, Event, EventLog,
    Contact, Medication, AdherenceLog, Report, SymptomSession,
    DoctorSummary, EmergencyToken, AuditEvent
)
from backend.app.security import hash_password
from backend.app.services.ai_client import build_structured_doctor_summary


def run_seed(db: Session = None):
    close_when_done = False
    if db is None:
        db = SessionLocal()
        close_when_done = True

    try:
        print("[SEED] Clearing existing records for fresh seed...")
        # Clear existing data in reverse dependency order
        db.query(AuditEvent).delete()
        db.query(EmergencyToken).delete()
        db.query(DoctorSummary).delete()
        db.query(SymptomSession).delete()
        db.query(Report).delete()
        db.query(AdherenceLog).delete()
        db.query(Medication).delete()
        db.query(Contact).delete()
        db.query(EventLog).delete()
        db.query(Event).delete()
        db.query(Reading).delete()
        db.query(Device).delete()
        db.query(Consent).delete()
        db.query(User).delete()
        db.commit()

        print("[SEED] Creating demo users (clearly fake Indian context)...")
        now = datetime.now(timezone.utc)

        # 1. Demo Patient: Ramesh Sharma
        patient = User(
            email="ramesh@example.com",
            hashed_password=hash_password("DemoPassword123!"),
            full_name="Ramesh Sharma",
            role="patient",
            age=68,
            gender="Male",
            blood_group="B+",
            allergies="Penicillin",
            chronic_conditions="Hypertension, Mild Type-2 Diabetes",
            phone="+91 98261 23456",
            emergency_contact="+91 94250 98765"
        )
        db.add(patient)

        # 2. Caregiver: Priya
        caregiver = User(
            email="priya@example.com",
            hashed_password=hash_password("DemoPassword123!"),
            full_name="Priya Sharma",
            role="caregiver",
            phone="+91 94250 98765"
        )
        db.add(caregiver)

        # 3. Doctor: Dr. Mehta
        doctor = User(
            email="dr.mehta@example.com",
            hashed_password=hash_password("DemoPassword123!"),
            full_name="Dr. Alok Mehta, MD",
            role="doctor",
            phone="+91 97551 11223"
        )
        db.add(doctor)

        # 4. Responder: Asha
        responder = User(
            email="asha@example.com",
            hashed_password=hash_password("DemoPassword123!"),
            full_name="Asha (EMT Jabalpur)",
            role="responder",
            phone="+91 98930 44556"
        )
        db.add(responder)

        # 5. Admin
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("DemoPassword123!"),
            full_name="System Administrator",
            role="admin"
        )
        db.add(admin)
        db.commit()

        # Refresh patient to get ID
        db.refresh(patient)

        # Consent record
        consent = Consent(
            user_id=patient.id,
            telemetry_collection=True,
            location_tracking=True,
            notifications_enabled=True,
            ai_assistance=True
        )
        db.add(consent)

        # IoT Device
        device = Device(
            device_id="ESP32-VITAL-01",
            user_id=patient.id,
            name="Ramesh's Wrist Sensor Unit",
            status="online",
            last_seen=now
        )
        db.add(device)
        db.commit()

        print("[SEED] Creating emergency contacts...")
        contacts = [
            Contact(
                user_id=patient.id,
                name="Priya Sharma",
                relationship_type="Daughter / Caregiver",
                phone="+91 94250 98765",
                email="priya.sharma@example.com",
                notify_sos=True,
                notify_warning=True,
                priority_order=1
            ),
            Contact(
                user_id=patient.id,
                name="Dr. Alok Mehta",
                relationship_type="Family Physician",
                phone="+91 97551 11223",
                email="dr.mehta@example.com",
                notify_sos=True,
                notify_warning=False,
                priority_order=2
            ),
            Contact(
                user_id=patient.id,
                name="Asha Ambulance Services",
                relationship_type="Local EMS",
                phone="112",
                notify_sos=True,
                notify_warning=True,
                priority_order=3
            )
        ]
        db.add_all(contacts)

        print("[SEED] Creating 7 days of realistic readings history...")
        # 7 days hourly readings + dense windows
        base_lat = 23.1815
        base_lng = 79.9864
        readings_batch = []

        for day in range(7, 0, -1):
            day_time = now - timedelta(days=day)
            for hour in range(0, 24, 2):  # Every 2 hours
                ts = day_time + timedelta(hours=hour)
                bpm = round(random.uniform(68, 82), 1)
                spo2 = round(random.uniform(96.5, 99.0), 1)
                temp = round(random.uniform(36.4, 37.0), 1)

                r = Reading(
                    device_id="ESP32-VITAL-01",
                    user_id=patient.id,
                    bpm=bpm,
                    spo2=spo2,
                    temp_c=temp,
                    lat=base_lat + random.uniform(-0.001, 0.001),
                    lng=base_lng + random.uniform(-0.001, 0.001),
                    signal_quality="good",
                    is_valid=True,
                    measured_at=ts,
                    received_at=ts + timedelta(seconds=1)
                )
                readings_batch.append(r)

        # Add recent dense readings in the last hour
        for m in range(20, 0, -1):
            ts = now - timedelta(minutes=m)
            r = Reading(
                device_id="ESP32-VITAL-01",
                user_id=patient.id,
                bpm=round(72 + random.uniform(-3, 3), 1),
                spo2=round(98 + random.uniform(-1, 1), 1),
                temp_c=round(36.6 + random.uniform(-0.2, 0.2), 1),
                lat=base_lat + 0.0002,
                lng=base_lng + 0.0001,
                signal_quality="good",
                is_valid=True,
                measured_at=ts,
                received_at=ts + timedelta(seconds=1)
            )
            readings_batch.append(r)

        db.add_all(readings_batch)

        print("[SEED] Creating 3 past events with status chains...")
        # Event 1: Manual SOS acknowledged
        ev1_time = now - timedelta(days=2, hours=3)
        event1 = Event(
            user_id=patient.id,
            device_id="ESP32-VITAL-01",
            event_type="sos_manual",
            severity="critical",
            status="acknowledged",
            title="EMERGENCY SOS: Panic Button Pressed",
            description="Manual panic button pressed by patient near home.",
            idempotency_key=f"sos_seed_{uuid.uuid4().hex[:8]}",
            lat=base_lat,
            lng=base_lng,
            map_url=f"https://www.google.com/maps?q={base_lat},{base_lng}",
            ack_token=uuid.uuid4().hex,
            acknowledged_at=ev1_time + timedelta(minutes=4),
            acknowledged_by="Caregiver Priya Sharma",
            created_at=ev1_time
        )
        db.add(event1)
        db.commit()
        db.refresh(event1)

        db.add_all([
            EventLog(event_id=event1.id, status="sent", channel="in_app", detail="In-app panic banner published", created_at=ev1_time),
            EventLog(event_id=event1.id, status="delivered", channel="telegram", detail="Simulated Telegram message delivered", created_at=ev1_time + timedelta(seconds=2)),
            EventLog(event_id=event1.id, status="acknowledged", channel="web_link", detail="Acknowledged by Priya via one-touch SMS link", created_at=ev1_time + timedelta(minutes=4))
        ])

        # Event 2: Automatic warning cancelled by patient
        ev2_time = now - timedelta(days=1, hours=8)
        event2 = Event(
            user_id=patient.id,
            device_id="ESP32-VITAL-01",
            event_type="warning_auto",
            severity="warning",
            status="resolved",
            title="Automatic Warning: Transient Tachycardia (Resolved)",
            description="Automatic, unconfirmed. High pulse >125 BPM detected following physical activity. Cancelled/dismissed.",
            idempotency_key=f"warn_seed_{uuid.uuid4().hex[:8]}",
            lat=base_lat,
            lng=base_lng,
            map_url=f"https://www.google.com/maps?q={base_lat},{base_lng}",
            ack_token=uuid.uuid4().hex,
            resolved_at=ev2_time + timedelta(minutes=10),
            resolved_by="Patient Ramesh Sharma",
            created_at=ev2_time
        )
        db.add(event2)
        db.commit()
        db.refresh(event2)

        db.add_all([
            EventLog(event_id=event2.id, status="created", channel="system", detail="Automatic warning generated after 30s abnormal pulse", created_at=ev2_time),
            EventLog(event_id=event2.id, status="resolved", channel="in_app", detail="Resolved: Patient took rest after climbing stairs", created_at=ev2_time + timedelta(minutes=10))
        ])

        # Event 3: Failed notification demonstration
        ev3_time = now - timedelta(hours=14)
        event3 = Event(
            user_id=patient.id,
            device_id="ESP32-VITAL-01",
            event_type="warning_auto",
            severity="warning",
            status="failed",
            title="Automatic Warning: Low Oxygen SpO2 89% (Delivery Failure)",
            description="Automatic unconfirmed warning. Simulated SMS carrier gateway timeout.",
            idempotency_key=f"fail_seed_{uuid.uuid4().hex[:8]}",
            lat=base_lat,
            lng=base_lng,
            map_url=f"https://www.google.com/maps?q={base_lat},{base_lng}",
            ack_token=uuid.uuid4().hex,
            created_at=ev3_time
        )
        db.add(event3)
        db.commit()
        db.refresh(event3)

        db.add_all([
            EventLog(event_id=event3.id, status="created", channel="system", detail="SpO2 dropped below 90% for 35 seconds", created_at=ev3_time),
            EventLog(event_id=event3.id, status="failed", channel="simulated_pipeline", detail="Carrier simulated error: Network timeout after 2 retries", created_at=ev3_time + timedelta(seconds=12))
        ])

        print("[SEED] Creating 4 medications with schedule and adherence...")
        meds = [
            Medication(
                user_id=patient.id,
                name="Telmisartan",
                strength="40 mg",
                form="Tablet",
                times_per_day=1,
                schedule_times=json.dumps(["08:00"]),
                duration_days=60,
                instructions="1 tablet daily after breakfast for blood pressure",
                is_verified=True,
                confidence_score=0.98
            ),
            Medication(
                user_id=patient.id,
                name="Metformin Hydrochloride",
                strength="500 mg",
                form="Tablet",
                times_per_day=2,
                schedule_times=json.dumps(["08:30", "20:30"]),
                duration_days=90,
                instructions="Take with meals twice daily",
                is_verified=True,
                confidence_score=0.96
            ),
            Medication(
                user_id=patient.id,
                name="Amlodipine",
                strength="5 mg",
                form="Tablet",
                times_per_day=1,
                schedule_times=json.dumps(["21:00"]),
                duration_days=30,
                instructions="1 tablet at bedtime",
                is_verified=True,
                confidence_score=0.94
            ),
            Medication(
                user_id=patient.id,
                name="Multivitamin & Minerals",
                strength="Standard",
                form="Capsule",
                times_per_day=1,
                schedule_times=json.dumps(["13:00"]),
                duration_days=30,
                instructions="1 capsule after lunch",
                is_verified=False,  # Unverified for demonstration
                confidence_score=0.74
            )
        ]
        db.add_all(meds)
        db.commit()

        # Seed adherence logs
        for m in meds[:3]:
            for d in range(5, 0, -1):
                scheduled_dt = now - timedelta(days=d, hours=2)
                action_choice = "taken" if random.random() > 0.15 else "skipped"
                db.add(AdherenceLog(
                    medication_id=m.id,
                    user_id=patient.id,
                    scheduled_time=scheduled_dt,
                    action=action_choice,
                    action_time=scheduled_dt + timedelta(minutes=15)
                ))
        db.commit()

        print("[SEED] Creating 2 sample laboratory reports...")
        rep1_data = [
            {"test_name": "Fasting Blood Glucose", "value": "114", "unit": "mg/dL", "reference_range": "70 - 100", "confidence": 0.98, "status": "verified"},
            {"test_name": "HbA1c", "value": "6.6", "unit": "%", "reference_range": "< 5.7 (Normal)", "confidence": 0.95, "status": "verified"},
            {"test_name": "Serum Creatinine", "value": "1.02", "unit": "mg/dL", "reference_range": "0.7 - 1.3", "confidence": 0.96, "status": "verified"}
        ]
        rep2_data = [
            {"test_name": "Lipid Profile - Total Cholesterol", "value": "208", "unit": "mg/dL", "reference_range": "< 200", "confidence": 0.91, "status": "verified"},
            {"test_name": "Triglycerides", "value": "175", "unit": "mg/dL", "reference_range": "< 150", "confidence": 0.72, "status": "unverified"},
            {"test_name": "HDL Cholesterol", "value": "44", "unit": "mg/dL", "reference_range": "> 40", "confidence": 0.89, "status": "verified"}
        ]
        reports = [
            Report(
                user_id=patient.id,
                filename="Diabetes_Renal_Panel_Sep2026.pdf",
                file_path="uploads/demo_panel_1.pdf",
                file_type="application/pdf",
                uploaded_at=now - timedelta(days=12),
                extracted_data=json.dumps(rep1_data),
                summary="Routine fasting blood sugar and HbA1c panel. Mild prediabetic range."
            ),
            Report(
                user_id=patient.id,
                filename="Lipid_Profile_Scan.jpg",
                file_path="uploads/demo_panel_2.jpg",
                file_type="image/jpeg",
                uploaded_at=now - timedelta(days=5),
                extracted_data=json.dumps(rep2_data),
                summary="Lipid profile strip photo. Low confidence on Triglycerides line."
            )
        ]
        db.add_all(reports)
        db.commit()

        print("[SEED] Creating 2 past symptom triage sessions...")
        sym1 = SymptomSession(
            user_id=patient.id,
            language="en",
            input_text="Mild dry cough and throat irritation since morning",
            rules_version="triage_rules_v1.0.0",
            red_flags_detected="[]",
            outcome="routine_consult",
            guidance="Schedule a routine consultation with a doctor. Stay well hydrated, rest adequately, and monitor vitals.",
            follow_up_questions=json.dumps(["Have you had any fever or chills?", "Are you able to swallow comfortably?"]),
            ai_explanation="Symptoms match common mild upper respiratory irritation. Non-emergency.",
            created_at=now - timedelta(days=3)
        )
        sym2 = SymptomSession(
            user_id=patient.id,
            language="hi",
            input_text="Seene mein dard aur saans lene me takleef ho rahi hai",
            rules_version="triage_rules_v1.0.0",
            red_flags_detected=json.dumps(["Severe chest pain / pressure (cardiac risk)", "Respiratory distress / breathlessness"]),
            outcome="emergency",
            guidance="🚨 CRITICAL WARNING: Potential emergency indicators detected. Do NOT wait. Call 112 immediately.",
            follow_up_questions=json.dumps(["Is an attendant present with the patient?", "Has an ambulance been dispatched?"]),
            ai_explanation="Immediate emergency protocol triggered due to chest pain and shortness of breath.",
            created_at=now - timedelta(days=1, hours=4)
        )
        db.add_all([sym1, sym2])
        db.commit()

        print("[SEED] Creating active Emergency Medical ID QR...")
        token_str = "demo-emergency-token-" + uuid.uuid4().hex[:12]
        em_token = EmergencyToken(
            user_id=patient.id,
            token=token_str,
            visible_fields=json.dumps(["blood_group", "allergies", "chronic_conditions", "emergency_contacts", "medications"]),
            expires_at=now + timedelta(hours=48),
            is_revoked=False,
            created_at=now
        )
        db.add(em_token)
        db.commit()

        print("[SEED] Creating initial AI Doctor Summary...")
        summary_doc = DoctorSummary(
            user_id=patient.id,
            title="Comprehensive Health Summary - Ramesh Sharma",
            structured_content=json.dumps(build_structured_doctor_summary(
                patient_info={
                    "full_name": patient.full_name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "blood_group": patient.blood_group,
                    "allergies": patient.allergies,
                    "chronic_conditions": patient.chronic_conditions
                },
                vitals_stats={"min_bpm": 68.0, "avg_bpm": 74.2, "max_bpm": 84.0, "min_spo2": 96.0, "avg_spo2": 98.1, "max_spo2": 99.0, "min_temp": 36.4, "avg_temp": 36.7, "max_temp": 37.0, "total_samples": 84},
                recent_readings=[{"bpm": 72.0, "spo2": 98.0, "temp_c": 36.7, "measured_at": now.isoformat()}],
                medications=[{"name": "Telmisartan", "strength": "40 mg", "form": "Tablet", "schedule_times": "[\"08:00\"]", "is_verified": True}],
                reports=[{"filename": "Diabetes_Renal_Panel_Sep2026.pdf", "extracted_data": rep1_data}],
                symptoms=[{"input_text": sym1.input_text, "outcome": sym1.outcome, "red_flags_detected": []}],
                events=[{"title": event1.title, "event_type": event1.event_type, "severity": event1.severity, "status": event1.status, "created_at": ev1_time.isoformat()}]
            )),
            share_token=uuid.uuid4().hex,
            share_expires_at=now + timedelta(days=3),
            created_at=now
        )
        db.add(summary_doc)
        db.commit()

        print("[SEED] Demo data successfully initialized!")
    finally:
        if close_when_done:
            db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    run_seed()
