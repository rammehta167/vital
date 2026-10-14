import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.warning_engine import evaluate_reading_for_warning, cancel_pending_candidate, is_abnormal
from backend.app.models import Reading


def test_abnormal_vital_evaluator():
    # Normal
    abnormal, reason = is_abnormal(72, 98, 36.6)
    assert not abnormal

    # Low SpO2
    abnormal, reason = is_abnormal(75, 89, 36.6)
    assert abnormal
    assert "Low oxygen" in reason

    # High BPM
    abnormal, reason = is_abnormal(135, 98, 36.6)
    assert abnormal
    assert "High pulse" in reason

    # High Temp
    abnormal, reason = is_abnormal(75, 98, 39.1)
    assert abnormal
    assert "Elevated temperature" in reason


@pytest.mark.asyncio
async def test_auto_warning_sustained_rule_and_cancel(db_session):
    now = datetime.now(timezone.utc)
    dev_id = "ESP32-TEST-WARN"

    # Reading 1 at t=0s (low oxygen, abnormal)
    r1 = Reading(
        device_id=dev_id,
        bpm=75.0,
        spo2=88.0,
        temp_c=36.6,
        signal_quality="good",
        is_valid=True,
        measured_at=now - timedelta(seconds=35)
    )
    db_session.add(r1)
    db_session.commit()

    cand1 = await evaluate_reading_for_warning(db_session, r1)
    assert cand1 is None  # Only 1 reading, cannot trigger yet

    # Reading 2 at t=35s (sustained >= 30s abnormal with good quality)
    r2 = Reading(
        device_id=dev_id,
        bpm=75.0,
        spo2=88.0,
        temp_c=36.6,
        signal_quality="good",
        is_valid=True,
        measured_at=now
    )
    db_session.add(r2)
    db_session.commit()

    cand2 = await evaluate_reading_for_warning(db_session, r2)
    assert cand2 is not None
    assert cand2["status"] == "countdown"
    assert cand2["countdown_seconds"] == 15
    candidate_id = cand2["candidate_id"]

    # Test user cancelling during the 15-second grace window
    cancelled = cancel_pending_candidate(dev_id, candidate_id)
    assert cancelled is True
