from typing import Optional
from sqlalchemy.orm import Session
from ..models import AuditEvent


def log_audit(
    db: Session,
    action: str,
    resource: str,
    details: Optional[str] = None,
    user_id: Optional[int] = None,
    actor_role: Optional[str] = None,
    ip_address: Optional[str] = None
):
    try:
        event = AuditEvent(
            user_id=user_id,
            actor_role=actor_role,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address
        )
        db.add(event)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[AUDIT LOG ERROR] Failed to record audit log: {e}")
