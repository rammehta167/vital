import uuid


def test_sos_idempotency_single_event(client):
    idemp_key = f"test_idemp_{uuid.uuid4().hex}"
    payload = {
        "device_id": "ESP32-VITAL-01",
        "lat": 23.1815,
        "lng": 79.9864,
        "idempotency_key": idemp_key,
        "details": "Panic button rapid double-click"
    }

    # First press
    resp1 = client.post("/api/v1/sos", json=payload)
    assert resp1.status_code == 200
    ev1 = resp1.json()

    # Rapid second press with same idempotency key
    resp2 = client.post("/api/v1/sos", json=payload)
    assert resp2.status_code == 200
    ev2 = resp2.json()

    # Must return exact same event ID without duplicating!
    assert ev1["id"] == ev2["id"]
    assert ev1["ack_token"] == ev2["ack_token"]


def test_event_status_chain_and_ack(client):
    idemp_key = f"test_chain_{uuid.uuid4().hex}"
    resp = client.post("/api/v1/sos", json={
        "device_id": "ESP32-VITAL-01",
        "lat": 23.1815,
        "lng": 79.9864,
        "idempotency_key": idemp_key,
        "details": "Status chain testing event"
    })
    assert resp.status_code == 200
    event = resp.json()
    ack_token = event["ack_token"]
    event_id = event["id"]

    # Initial status should be delivered (or sent)
    assert event["status"] in ("sent", "delivered")

    # Acknowledge via token link
    ack_resp = client.get(f"/api/v1/events/ack/{ack_token}")
    assert ack_resp.status_code == 200
    ack_data = ack_resp.json()
    assert ack_data["status"] == "acknowledged"

    # Verify event status in DB
    get_resp = client.get(f"/api/v1/events/{event_id}")
    assert get_resp.status_code == 200
    updated_ev = get_resp.json()
    assert updated_ev["status"] == "acknowledged"
    assert updated_ev["acknowledged_at"] is not None

    # Resolve event
    res_resp = client.post(f"/api/v1/events/{event_id}/resolve", json={
        "resolved_by": "Dr. Mehta",
        "notes": "Patient attended and stabilized"
    })
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["status"] == "resolved"
    assert res_data["resolved_at"] is not None
