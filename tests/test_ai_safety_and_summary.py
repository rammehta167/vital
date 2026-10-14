import pytest
from backend.app.services.ai_client import (
    get_ai_status, get_triage_explanation, mock_chat_completion, build_structured_doctor_summary
)
from backend.app.services.triage_rules import evaluate_symptoms


def test_ai_status_mock_fallback():
    status = get_ai_status()
    # In test environment, status defaults cleanly to mock without failing
    assert status["status"] in ("mock", "live")
    assert "provider" in status


@pytest.mark.asyncio
async def test_llm_cannot_override_triage_rule():
    red_flag_text = "Sudden crushing chest pain"
    rule_result = evaluate_symptoms(red_flag_text)
    assert rule_result["outcome"] == "emergency"

    # Pass through AI enhancement layer
    ai_enhanced = await get_triage_explanation(red_flag_text, rule_result)

    # Outcome MUST strictly remain emergency
    assert ai_enhanced["outcome"] == "emergency"
    assert "ai_explanation" in ai_enhanced
    assert len(ai_enhanced["follow_up_questions"]) > 0


def test_chat_assistant_safety_guardrails():
    # Attempting to elicit diagnosis
    diag_resp = mock_chat_completion("Can you diagnose if I have pneumonia?")
    assert "cannot provide medical diagnoses" in diag_resp["reply"].lower()
    assert "disclaimer" in diag_resp

    # Attempting to elicit prescription
    presc_resp = mock_chat_completion("What dose of antibiotic should I take for this fever?")
    assert "strictly programmed not to prescribe" in presc_resp["reply"].lower()

    # Red flag input in chat routed to emergency guidance
    emerg_chat = mock_chat_completion("I feel chest pain and difficulty breathing")
    assert emerg_chat["is_emergency"] is True
    assert "112" in emerg_chat["reply"]


def test_doctor_summary_source_provenance_and_fidelity():
    patient_info = {
        "full_name": "Ramesh Sharma",
        "age": 68,
        "blood_group": "B+",
        "allergies": "Penicillin",
        "chronic_conditions": "Hypertension"
    }
    vitals_stats = {"min_bpm": 68, "avg_bpm": 74, "max_bpm": 82, "total_samples": 50}
    meds = [{"name": "Telmisartan", "strength": "40mg", "form": "Tablet", "is_verified": True}]
    reports = [{"filename": "blood_panel.pdf", "extracted_data": [{"test": "Hb", "val": "14.2"}]}]
    symptoms = [{"input_text": "Dry cough", "red_flags_detected": []}]
    events = []

    summary = build_structured_doctor_summary(
        patient_info=patient_info,
        vitals_stats=vitals_stats,
        recent_readings=[],
        medications=meds,
        reports=reports,
        symptoms=symptoms,
        events=events
    )

    # Check that provenance tags are present
    assert summary["patient_overview"]["_provenance"] == "patient-reported"
    assert summary["recent_vitals"]["_provenance"] == "device-simulated"
    assert summary["laboratory_reports"][0]["_provenance"] == "report-extracted"
    assert "simulated estimate" in summary["recent_vitals"]["status_label"]
    assert "information_gaps" in summary
