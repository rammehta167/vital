from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Device, AuditEvent
from ..schemas import UserResponse, DeviceResponse, AuditEventResponse, SystemHealthResponse, MessageResponse
from ..security import get_current_user, require_roles
from ..services.ai_client import get_ai_status
from ..services.notifications import set_simulated_failure_toggle, get_simulated_failure_toggle
from simulator.simulator import global_simulator

router = APIRouter(prefix="/api/v1/admin", tags=["Administration & Health"])


@router.get("/health", response_model=SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    ai_info = get_ai_status()
    db_ok = True
    try:
        db.query(User).count()
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "version": "1.0.0-prototype",
        "ai_status": ai_info["status"],
        "ai_provider": ai_info["provider"],
        "active_device_connected": global_simulator.is_running,
        "simulator_active": global_simulator.is_running,
        "database_connected": db_ok,
        "timestamp": datetime.now(timezone.utc)
    }


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


@router.get("/audit-logs", response_model=List[AuditEventResponse])
def get_audit_logs(
    action: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if action:
        query = query.filter(AuditEvent.action == action)
    logs = query.order_by(AuditEvent.id.desc()).limit(limit).all()
    return logs


@router.get("/notification-failure-toggle")
def get_notification_failure_status():
    return {"simulate_failure": get_simulated_failure_toggle()}


@router.post("/notification-failure-toggle")
def toggle_notification_failure(
    enabled: bool,
    current_user: User = Depends(get_current_user)
):
    set_simulated_failure_toggle(enabled)
    return {
        "simulate_failure": enabled,
        "message": f"Simulated notification failure is now {'ENABLED' if enabled else 'DISABLED'}."
    }


@router.post("/reset-demo-data", response_model=MessageResponse)
def reset_demo_data(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    from seed.seed import run_seed
    run_seed(db)
    return {
        "message": "Demo data successfully re-seeded with Ramesh Sharma profile, vitals history, and alerts.",
        "detail": "Educational Indian context dataset restored."
    }
