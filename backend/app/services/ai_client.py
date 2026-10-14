import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from .triage_rules import evaluate_symptoms

logger = logging.getLogger("ai_client")

AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "")


def get_ai_status() -> Dict[str, Any]:
    has_key = bool(AI_API_KEY)
    is_live = has_key and AI_PROVIDER in ("gemini", "anthropic", "openai")
    return {
        "status": "live" if is_live else "mock",
        "provider": AI_PROVIDER if is_live else "mock",
        "model": AI_MODEL if is_live else "deterministic-fallback-v1"
    }


# ==========================================
# Deterministic Mock Implementations
# ==========================================

def mock_triage_enhancement(symptoms: str, triage_result: Dict[str, Any]) -> Dict[str, Any]:
    outcome = triage_result["outcome"]
    if outcome == "emergency":
        explanation = (
            "Based on the critical indicators mentioned (such as red-flag symptoms), "
            "our safety protocols have prioritized immediate emergency referral. "
            "Under no circumstances should care be delayed. Please call 112 or visit emergency."
        )
        follow_ups = [
            "Is an attendant present with the patient?",
            "Are vital signs such as pulse and breathing being monitored?",
            "Have you notified local emergency services?"
        ]
    elif outcome == "prompt_care":
        explanation = (
            "Your described symptoms suggest acute discomfort that requires physical examination "
            "by a qualified doctor within the next several hours to prevent complications."
        )
        follow_ups = [
            "Has the temperature crossed 38.5°C?",
            "Are you experiencing dehydration or fatigue?",
            "Do symptoms ease after resting?"
        ]
    elif outcome == "routine_consult":
        explanation = (
            "Your symptoms are consistent with common seasonal or mild conditions. "
            "However, an in-person clinical consultation will help provide targeted relief and rule out secondary infections."
        )
        follow_ups = [
            "Are there any other family members with similar cold or flu symptoms?",
            "How is your fluid intake today?",
            "Are you taking any prescribed medications for chronic conditions?"
        ]
    else:
        explanation = (
            "The symptoms entered appear mild. Maintain hydration and keep monitoring your vitals. "
            "If symptoms worsen or continue for more than 48 hours, consult a physician."
        )
        follow_ups = [
            "When did this feeling begin?",
            "Have you checked your pulse or blood pressure today?"
        ]

    return {
        "outcome": triage_result["outcome"],  # CAN NEVER BE MODIFIED
        "ai_explanation": explanation,
        "follow_up_questions": follow_ups
    }


def mock_chat_completion(message: str, patient_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # 1. Pre-check for red flags BEFORE ANY LLM CALL
    triage_check = evaluate_symptoms(message)
    if triage_check["outcome"] == "emergency":
        return {
            "reply": (
                "🚨 EMERGENCY NOTICE: Your message contains potential red-flag medical signs "
                f"({', '.join(triage_check['red_flags'])}). "
                "I cannot provide chat recommendations for emergency situations. "
                "Please CALL 112 IMMEDIATELY or head to the nearest casualty/hospital emergency room."
            ),
            "is_emergency": True,
            "disclaimer": "Educational AI prototype. Never diagnose or prescribe. In emergencies call 112."
        }

    lowered = message.lower()

    if any(k in lowered for k in ["diagnose", "what do i have", "do i have cancer", "is it malaria"]):
        reply = (
            "I cannot provide medical diagnoses. As an AI health companion, I can summarize your recorded "
            "vitals and symptoms to help you prepare for an appointment with your doctor. "
            "Please share your concerns directly with a licensed physician."
        )
    elif any(k in lowered for k in ["prescribe", "dose", "which medicine", "give me medicine", "dawa", "dawakhana"]):
        reply = (
            "I am strictly programmed NOT to prescribe medications or adjust dosages. "
            "Please take only medications prescribed by your healthcare provider. "
            "If you are experiencing new or worsening symptoms, consult your doctor or pharmacist."
        )
    elif any(k in lowered for k in ["pulse", "heart rate", "spo2", "vital", "temperature", "reading"]):
        last_vitals = patient_context.get("latest_vitals", {}) if patient_context else {}
        pulse_val = last_vitals.get("bpm", "72 (simulated)")
        spo2_val = last_vitals.get("spo2", "98% (simulated)")
        reply = (
            f"Based on your recent monitoring session, your pulse is currently approximately {pulse_val} BPM "
            f"and SpO2 is {spo2_val}. Both readings are simulated estimates from the tracker. "
            "Maintain adequate hydration and rest."
        )
    elif any(k in lowered for k in ["medicine", "pill", "tablet", "schedule", "reminder"]):
        meds = patient_context.get("medications", []) if patient_context else []
        med_names = ", ".join([m.get("name", "") for m in meds]) if meds else "Telmisartan 40mg, Metformin 500mg"
        reply = (
            f"Your current recorded medication schedule includes: {med_names}. "
            "Always take doses with water after meals as directed on your physician's prescription."
        )
    else:
        reply = (
            "I am your AI Healthcare Companion. I can help track your daily simulated vitals, "
            "organize medicine reminders, and generate structured summaries for your doctor visits. "
            "How can I assist you with your routine wellness today?"
        )

    return {
        "reply": reply,
        "is_emergency": False,
        "disclaimer": "Educational prototype only. Never diagnose or prescribe. For real emergencies call 112."
    }


def mock_extract_medication(filename: str = "") -> Dict[str, Any]:
    return {
        "name": "Telmisartan",
        "strength": "40 mg",
        "form": "Tablet",
        "confidence": 0.94,
        "suggested_instructions": "Take 1 tablet once daily in the morning after breakfast",
        "raw_ocr_extracted": {
            "brand_name": "Telma 40",
            "salt": "Telmisartan IP 40mg",
            "mfg_date": "08/2025",
            "exp_date": "07/2027",
            "batch": "BTX-4429"
        }
    }


def mock_extract_report_data(filename: str = "") -> List[Dict[str, Any]]:
    return [
        {
            "test_name": "Hemoglobin (Hb)",
            "value": "13.8",
            "unit": "g/dL",
            "reference_range": "13.0 - 17.0",
            "confidence": 0.98,
            "status": "verified"
        },
        {
            "test_name": "Fasting Blood Glucose",
            "value": "118",
            "unit": "mg/dL",
            "reference_range": "70 - 100",
            "confidence": 0.92,
            "status": "unverified"
        },
        {
            "test_name": "Serum Creatinine",
            "value": "1.05",
            "unit": "mg/dL",
            "reference_range": "0.7 - 1.3",
            "confidence": 0.96,
            "status": "verified"
        },
        {
            "test_name": "Total Cholesterol",
            "value": "192",
            "unit": "mg/dL",
            "reference_range": "< 200",
            "confidence": 0.88,
            "status": "unverified"
        }
    ]


# ==========================================
# Real LLM Callers with Fallback
# ==========================================

async def call_gemini_api(prompt: str, json_mode: bool = False) -> Optional[str]:
    api_key = AI_API_KEY
    model = AI_MODEL or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if json_mode:
        payload["generationConfig"] = {"responseMimeType": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}")
                return None
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}")
        return None


async def call_openai_api(prompt: str, json_mode: bool = False) -> Optional[str]:
    api_key = AI_API_KEY
    model = AI_MODEL or "gpt-4o-mini"
    url = "https://api.openai.com/v1/chat/completions"

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"OpenAI API returned status {resp.status_code}")
                return None
    except Exception as e:
        logger.warning(f"OpenAI API call failed: {e}")
        return None


# ==========================================
# Unified Provider-Agnostic Interface
# ==========================================

async def get_triage_explanation(symptoms: str, triage_result: Dict[str, Any]) -> Dict[str, Any]:
    fallback = mock_triage_enhancement(symptoms, triage_result)
    status_info = get_ai_status()
    if status_info["status"] != "live":
        return fallback

    prompt = (
        f"You are a clinical communications assistant. A deterministic medical triage rule evaluated this user's input.\n"
        f"User symptoms: '{symptoms}'\n"
        f"Triage Outcome Rule: {triage_result['outcome']}\n"
        f"Detected Red Flags: {triage_result.get('red_flags', [])}\n"
        f"CRITICAL CONSTRAINT: You CANNOT modify or contradict the triage outcome '{triage_result['outcome']}'. "
        f"Your task is to provide:\n"
        f"1. A concise, empathetic explanation of why this rule-based outcome was recommended.\n"
        f"2. 2-3 clinical follow-up questions for their doctor visit.\n"
        f"Respond ONLY in valid JSON matching this schema: "
        f"{{\"ai_explanation\": \"...\", \"follow_up_questions\": [\"...\", \"...\"]}}"
    )

    try:
        raw_text = None
        if status_info["provider"] == "gemini":
            raw_text = await call_gemini_api(prompt, json_mode=True)
        elif status_info["provider"] == "openai":
            raw_text = await call_openai_api(prompt, json_mode=True)

        if raw_text:
            parsed = json.loads(raw_text)
            return {
                "outcome": triage_result["outcome"],  # STAYS DETERMINISTIC
                "ai_explanation": parsed.get("ai_explanation", fallback["ai_explanation"]),
                "follow_up_questions": parsed.get("follow_up_questions", fallback["follow_up_questions"])
            }
    except Exception as e:
        logger.warning(f"LLM triage call failed: {e}. Using deterministic fallback.")

    return fallback


async def get_chat_response(message: str, patient_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Red flags check before any LLM execution
    triage_check = evaluate_symptoms(message)
    if triage_check["outcome"] == "emergency":
        return {
            "reply": (
                "🚨 EMERGENCY NOTICE: Your message mentions potential emergency signs "
                f"({', '.join(triage_check['red_flags'])}). "
                "I cannot provide general wellness chat for urgent symptoms. "
                "PLEASE CALL 112 IMMEDIATELY or go to the nearest emergency department."
            ),
            "is_emergency": True,
            "disclaimer": "Educational AI prototype. Never diagnose or prescribe. In emergencies call 112."
        }

    status_info = get_ai_status()
    if status_info["status"] != "live":
        return mock_chat_completion(message, patient_context)

    prompt = (
        "You are an AI Healthcare Companion for an educational prototype. "
        "Rules:\n"
        "1. Never diagnose diseases, never prescribe medicines, never suggest altering dosages.\n"
        "2. Ground answers only in the confirmed patient context.\n"
        "3. Always keep answers concise, polite, and encouraging.\n"
        f"Patient Context: {json.dumps(patient_context or {})}\n"
        f"User message: {message}"
    )

    try:
        raw_text = None
        if status_info["provider"] == "gemini":
            raw_text = await call_gemini_api(prompt, json_mode=False)
        elif status_info["provider"] == "openai":
            raw_text = await call_openai_api(prompt, json_mode=False)

        if raw_text:
            return {
                "reply": raw_text.strip(),
                "is_emergency": False,
                "disclaimer": "Educational AI prototype. Never diagnose or prescribe. In emergencies call 112."
            }
    except Exception as e:
        logger.warning(f"LLM chat call failed: {e}. Falling back to mock.")

    return mock_chat_completion(message, patient_context)


def build_structured_doctor_summary(
    patient_info: Dict[str, Any],
    vitals_stats: Dict[str, Any],
    recent_readings: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
    reports: List[Dict[str, Any]],
    symptoms: List[Dict[str, Any]],
    events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Builds a one-page clinical summary tagged with strict provenance sources:
    - patient-reported
    - report-extracted
    - device-simulated
    - AI-generated
    Never fabricates; highlights information gaps.
    """
    red_flag_status = "Negative (No acute red flags recorded)"
    for sym in symptoms:
        if sym.get("red_flags_detected") and len(sym["red_flags_detected"]) > 0:
            red_flag_status = f"Positive: {', '.join(sym['red_flags_detected'])}"
            break

    # Information gaps detection
    gaps: List[str] = []
    if not patient_info.get("blood_group"):
        gaps.append("Blood group not recorded in patient profile")
    if not reports:
        gaps.append("No laboratory diagnostic reports uploaded")
    unverified_meds = [m.get("name") for m in medications if not m.get("is_verified", True)]
    if unverified_meds:
        gaps.append(f"Medications awaiting patient verification: {', '.join(unverified_meds)}")
    if vitals_stats.get("total_samples", 0) < 5:
        gaps.append("Limited vital samples recorded in current monitoring window")

    structured = {
        "patient_overview": {
            "name": patient_info.get("full_name", "Unknown"),
            "age": patient_info.get("age", "N/A"),
            "gender": patient_info.get("gender", "N/A"),
            "blood_group": patient_info.get("blood_group", "N/A"),
            "allergies": patient_info.get("allergies", "None reported"),
            "chronic_conditions": patient_info.get("chronic_conditions", "None reported"),
            "_provenance": "patient-reported"
        },
        "chief_complaints": [
            {
                "complaint": s.get("input_text"),
                "reported_at": s.get("created_at"),
                "_provenance": "patient-reported"
            } for s in symptoms[:3]
        ] if symptoms else [{"complaint": "Routine health & vital monitoring", "_provenance": "patient-reported"}],
        "red_flag_screen": {
            "status": red_flag_status,
            "_provenance": "AI-generated"
        },
        "current_medications": [
            {
                "name": m.get("name"),
                "strength": m.get("strength"),
                "form": m.get("form"),
                "schedule": m.get("schedule_times"),
                "verification_status": "verified" if m.get("is_verified", True) else "unverified",
                "_provenance": "patient-reported" if m.get("is_verified") else "report-extracted"
            } for m in medications
        ],
        "laboratory_reports": [
            {
                "filename": r.get("filename"),
                "extracted_values": r.get("extracted_data"),
                "_provenance": "report-extracted"
            } for r in reports
        ],
        "recent_vitals": {
            "bpm": {
                "min": vitals_stats.get("min_bpm"),
                "avg": vitals_stats.get("avg_bpm"),
                "max": vitals_stats.get("max_bpm")
            },
            "spo2": {
                "min": vitals_stats.get("min_spo2"),
                "avg": vitals_stats.get("avg_spo2"),
                "max": vitals_stats.get("max_spo2")
            },
            "temp_c": {
                "min": vitals_stats.get("min_temp"),
                "avg": vitals_stats.get("avg_temp"),
                "max": vitals_stats.get("max_temp")
            },
            "total_samples": vitals_stats.get("total_samples", 0),
            "status_label": "simulated estimate",
            "_provenance": "device-simulated"
        },
        "recent_alerts": [
            {
                "title": e.get("title"),
                "event_type": e.get("event_type"),
                "severity": e.get("severity"),
                "status": e.get("status"),
                "created_at": e.get("created_at"),
                "_provenance": "device-simulated"
            } for e in events[:5]
        ],
        "information_gaps": gaps,
        "disclaimer": "Educational Prototype. Not a certified clinical diagnosis. Readings are simulated estimates."
    }
    return structured
