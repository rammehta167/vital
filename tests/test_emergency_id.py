import uuid
from datetime import datetime, timezone, timedelta
from backend.app.models import EmergencyToken, User


def test_emergency_token_flow_and_revocation(client, db_session):
    # Get demo patient
    patient = db_session.query(User).filter(User.role == "patient").first()
    assert patient is not None

    # Login as patient
    login_resp = client.post("/api/v1/auth/login", json={
        "email": patient.email,
        "password": "DemoPassword123!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate QR token
    gen_resp = client.post("/api/v1/emergency-id/generate", json={
        "visible_fields": ["blood_group", "allergies", "chronic_conditions"],
        "expire_hours": 12
    }, headers=headers)
    assert gen_resp.status_code == 200
    qr_data = gen_resp.json()
    token_str = qr_data["token"]
    assert "data:image/png;base64," in qr_data["qr_code_base64"]

    # Public scan by first responder
    scan_resp = client.get(f"/api/v1/emergency-id/public/{token_str}")
    assert scan_resp.status_code == 200
    public_card = scan_resp.json()
    assert public_card["patient_name"] == "Ramesh Sharma"
    assert public_card["blood_group"] == "B+"
    assert public_card["allergies"] == "Penicillin"

    # Verify access log was recorded
    logs_resp = client.get("/api/v1/emergency-id/access-logs", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) > 0

    # Revoke QR token
    rev_resp = client.post("/api/v1/emergency-id/revoke", headers=headers)
    assert rev_resp.status_code == 200

    # Scans after revocation must fail with 404
    scan_revoked = client.get(f"/api/v1/emergency-id/public/{token_str}")
    assert scan_revoked.status_code == 404
