import os
import time
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Event, EventLog, Contact, User

SIMULATE_FAILURE_ENV = os.getenv("SIMULATE_NOTIFICATION_FAILURE", "false").lower() in ("true", "1", "yes")

# Global runtime toggle for UI control
RUN_TIME_SIMULATE_FAILURE = SIMULATE_FAILURE_ENV


def set_simulated_failure_toggle(value: bool):
    global RUN_TIME_SIMULATE_FAILURE
    RUN_TIME_SIMULATE_FAILURE = value


def get_simulated_failure_toggle() -> bool:
    return RUN_TIME_SIMULATE_FAILURE


def record_log(db: Session, event_id: int, status: str, channel: str, detail: str):
    log = EventLog(
        event_id=event_id,
        status=status,
        channel=channel,
        detail=detail,
        created_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()


def dispatch_emergency_notifications(
    db: Session,
    event: Event,
    base_url: str = "http://localhost:8000"
) -> bool:
    """
    Dispatches notifications across configured channels:
    1. In-App Notification (channel: in_app)
    2. Telegram Bot (channel: telegram) - real if token provided, else simulated
    3. SMS (channel: sms_simulated) - simulated adapter
    4. Email (channel: email_simulated) - simulated adapter

    Updates Event status chain:
    Created -> Sent -> Delivered (or Failed if test toggle active)
    """
    event_id = event.id
    ack_url = f"{base_url}/ack/{event.ack_token}" if event.ack_token else f"{base_url}"

    # 1. In-App notification
    record_log(db, event_id, "sent", "in_app", f"In-app alert published. Ack Link: {ack_url}")
    record_log(db, event_id, "delivered", "in_app", "In-app alert displayed on active dashboard listeners.")

    # Check simulated failure toggle
    if RUN_TIME_SIMULATE_FAILURE:
        record_log(db, event_id, "failed", "simulated_pipeline", "[TEST MODE] Simulated notification failure triggered by user switch.")
        event.status = "failed"
        db.commit()
        return False

    # Get contacts for this user
    contacts: List[Contact] = []
    if event.user_id:
        contacts = db.query(Contact).filter(Contact.user_id == event.user_id).order_by(Contact.priority_order).all()

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    default_telegram_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    alert_text = (
        f"🚨 EMERGENCY ALERT: {event.title}\n"
        f"Severity: {event.severity.upper()}\n"
        f"{event.description or ''}\n"
        f"Live Map: {event.map_url or 'N/A'}\n"
        f"Acknowledge here: {ack_url}\n"
        f"⚠️ Educational Prototype - Not a medical device. For real emergency call 112."
    )

    all_delivered = True

    # 2. Telegram Dispatch
    telegram_target = default_telegram_chat
    if contacts:
        for c in contacts:
            if c.telegram_chat_id:
                telegram_target = c.telegram_chat_id
                break

    if telegram_bot_token and telegram_target:
        sent_ok = False
        # Retry with backoff (up to 2 retries)
        for attempt in range(1, 3):
            try:
                record_log(db, event_id, "sent", "telegram", f"Sending Telegram to chat {telegram_target} (attempt {attempt})...")
                resp = httpx.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    json={"chat_id": telegram_target, "text": alert_text},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    sent_ok = True
                    record_log(db, event_id, "delivered", "telegram", f"Telegram message successfully delivered to chat ID {telegram_target}.")
                    break
                else:
                    record_log(db, event_id, "failed", "telegram", f"Telegram API returned {resp.status_code}: {resp.text}")
            except Exception as exc:
                record_log(db, event_id, "failed", "telegram", f"Telegram network error on attempt {attempt}: {str(exc)}")
                time.sleep(0.5)

        if not sent_ok:
            all_delivered = False
    else:
        # Simulated Telegram
        record_log(db, event_id, "sent", "telegram", f"[SIMULATED] Would send Telegram to configured chat. Ack URL: {ack_url}")
        record_log(db, event_id, "delivered", "telegram", "[SIMULATED] Mock Telegram message delivered.")

    # 3. SMS Simulated Adapter
    for contact in contacts:
        if contact.notify_sos or (event.severity == "warning" and contact.notify_warning):
            record_log(
                db, event_id, "sent", "sms_simulated",
                f"[SIMULATED SMS] Sending SMS to {contact.name} ({contact.phone}): '{event.title} - Ack: {ack_url}'"
            )
            record_log(
                db, event_id, "delivered", "sms_simulated",
                f"[SIMULATED SMS] Carrier simulated delivery to {contact.phone} confirmed."
            )

    # 4. Email Simulated Adapter
    for contact in contacts:
        if contact.email:
            record_log(
                db, event_id, "sent", "email_simulated",
                f"[SIMULATED EMAIL] Queuing alert email to {contact.email} with triage details."
            )
            record_log(
                db, event_id, "delivered", "email_simulated",
                f"[SIMULATED EMAIL] SMTP mock server delivered alert email to {contact.email}."
            )

    event.status = "delivered" if all_delivered else "sent"
    db.commit()
    return True
