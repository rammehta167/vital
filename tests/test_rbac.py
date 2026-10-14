def test_demo_login_all_roles(client):
    roles = ["patient", "caregiver", "responder", "doctor", "admin"]
    for role in roles:
        resp = client.post("/api/v1/auth/demo-login", json={"role": role})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["role"] == role


def test_rbac_admin_routes_forbidden_for_patient(client):
    # Patient login
    pat_resp = client.post("/api/v1/auth/demo-login", json={"role": "patient"})
    pat_token = pat_resp.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    # Attempt to view admin audit logs
    audit_resp = client.get("/api/v1/admin/audit-logs", headers=pat_headers)
    assert audit_resp.status_code == 403

    # Attempt to list all users
    users_resp = client.get("/api/v1/admin/users", headers=pat_headers)
    assert users_resp.status_code == 403


def test_rbac_admin_routes_allowed_for_admin(client):
    # Admin login
    admin_resp = client.post("/api/v1/auth/demo-login", json={"role": "admin"})
    admin_token = admin_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin accesses users
    users_resp = client.get("/api/v1/admin/users", headers=admin_headers)
    assert users_resp.status_code == 200
    assert len(users_resp.json()) > 0
