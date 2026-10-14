from datetime import datetime, timezone, timedelta


def test_reading_with_invalid_device_key(client):
    payload = {
        "device_id": "ESP32-VITAL-01",
        "bpm": 75.0,
        "spo2": 98.0,
        "temp_c": 36.6,
        "signal_quality": "good"
    }
    # No header
    resp = client.post("/api/v1/readings", json=payload)
    assert resp.status_code == 401

    # Wrong header
    resp2 = client.post("/api/v1/readings", json=payload, headers={"X-Device-Key": "wrong-key"})
    assert resp2.status_code == 401


def test_reading_with_valid_device_key(client):
    payload = {
        "device_id": "ESP32-VITAL-01",
        "bpm": 74.5,
        "spo2": 98.2,
        "temp_c": 36.7,
        "signal_quality": "good"
    }
    resp = client.post("/api/v1/readings", json=payload, headers={"X-Device-Key": "demo-device-key-change-me"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bpm"] == 74.5
    assert data["spo2"] == 98.2
    assert data["is_valid"] is True


def test_no_finger_handling(client):
    payload = {
        "device_id": "ESP32-VITAL-01",
        "bpm": None,
        "spo2": None,
        "temp_c": 36.5,
        "signal_quality": "no_finger"
    }
    resp = client.post("/api/v1/readings", json=payload, headers={"X-Device-Key": "demo-device-key-change-me"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bpm"] is None
    assert data["spo2"] is None
    assert data["signal_quality"] == "no_finger"
    assert data["is_valid"] is False


def test_stale_detection(client):
    # Insert old reading with timestamp 25 seconds ago
    old_time = datetime.now(timezone.utc) - timedelta(seconds=25)
    payload = {
        "device_id": "ESP32-VITAL-01",
        "bpm": 72.0,
        "spo2": 98.0,
        "temp_c": 36.6,
        "signal_quality": "good",
        "ts": old_time.isoformat()
    }
    client.post("/api/v1/readings", json=payload, headers={"X-Device-Key": "demo-device-key-change-me"})

    # Check latest endpoint
    resp = client.get("/api/v1/readings/latest?device_id=ESP32-VITAL-01")
    assert resp.status_code == 200
    data = resp.json()
    assert "reading" in data
    # Message confirms simulated estimate
    assert "simulated estimate" in data["message"].lower()
