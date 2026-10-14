import uuid
from backend.app.services.notifications import (
    set_simulated_failure_toggle, get_simulated_failure_toggle, dispatch_emergency_notifications
)
from backend.app.models import Event


def test_notification_simulated_failure_toggle(db_session):
    # Enable failure simulation
    set_simulated_failure_toggle(True)
    assert get_simulated_failure_toggle() is True

    test_event = Event(
        device_id="ESP32-TEST",
        event_type="sos_manual",
        severity="critical",
        status="created",
        title="Test Simulated Failure",
        ack_token=uuid.uuid4().hex
    )
    db_session.add(test_event)
    db_session.commit()
    db_session.refresh(test_event)

    delivered = dispatch_emergency_notifications(db_session, test_event)
    assert delivered is False
    assert test_event.status == "failed"

    # Reset failure toggle
    set_simulated_failure_toggle(False)
    assert get_simulated_failure_toggle() is False

    test_event2 = Event(
        device_id="ESP32-TEST",
        event_type="sos_manual",
        severity="critical",
        status="created",
        title="Test Normal Delivery",
        ack_token=uuid.uuid4().hex
    )
    db_session.add(test_event2)
    db_session.commit()
    db_session.refresh(test_event2)

    delivered2 = dispatch_emergency_notifications(db_session, test_event2)
    assert delivered2 is True
    assert test_event2.status in ("sent", "delivered")
