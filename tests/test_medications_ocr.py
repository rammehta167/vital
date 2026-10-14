import io


def test_medicine_ocr_requires_user_confirmation(client):
    # Login as patient
    login_resp = client.post("/api/v1/auth/demo-login", json={"role": "patient"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload mock image of medicine strip
    file_bytes = b"fake-jpeg-image-bytes-of-strip"
    files = {"file": ("strip.jpg", io.BytesIO(file_bytes), "image/jpeg")}

    scan_resp = client.post("/api/v1/medications/scan-strip", files=files, headers=headers)
    assert scan_resp.status_code == 200
    data = scan_resp.json()

    assert data["requires_verification"] is True
    assert "name" in data
    assert "confidence" in data
    assert "disclaimer" in data

    # Now verify saving with explicit user confirmation
    add_resp = client.post("/api/v1/medications", json={
        "name": data["name"],
        "strength": data["strength"],
        "form": data["form"],
        "times_per_day": 1,
        "schedule_times": ["08:00"],
        "duration_days": 30,
        "instructions": data["suggested_instructions"],
        "is_verified": True  # Confirmed by user!
    }, headers=headers)

    assert add_resp.status_code == 200
    saved_med = add_resp.json()
    assert saved_med["name"] == data["name"]
    assert saved_med["is_verified"] is True
