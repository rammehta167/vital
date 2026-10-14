from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Reading, Medication
from ..schemas import ChatRequest, ChatResponse
from ..security import get_optional_current_user
from ..services.ai_client import get_chat_response

router = APIRouter(prefix="/api/v1/chat", tags=["AI Health Chat Companion"])


@router.post("", response_model=ChatResponse)
async def chat_with_companion(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    patient_context = {}
    if current_user:
        latest_reading = db.query(Reading).filter(Reading.user_id == current_user.id).order_by(Reading.id.desc()).first()
        meds = db.query(Medication).filter(Medication.user_id == current_user.id).all()
        patient_context = {
            "name": current_user.full_name,
            "chronic_conditions": current_user.chronic_conditions,
            "allergies": current_user.allergies,
            "latest_vitals": {
                "bpm": latest_reading.bpm if latest_reading else 72,
                "spo2": latest_reading.spo2 if latest_reading else 98
            },
            "medications": [{"name": m.name, "strength": m.strength} for m in meds]
        }

    response = await get_chat_response(req.message, patient_context)
    return response
