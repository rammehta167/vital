import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import SymptomSession, User
from ..schemas import SymptomInput, SymptomResponse
from ..security import get_current_user, get_optional_current_user
from ..services.triage_rules import evaluate_symptoms, RULES_VERSION
from ..services.ai_client import get_triage_explanation

router = APIRouter(prefix="/api/v1/symptoms", tags=["Clinical Triage & Symptoms"])


@router.get("", response_model=List[SymptomResponse])
def get_symptom_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(SymptomSession).filter(SymptomSession.user_id == current_user.id).order_by(SymptomSession.id.desc()).all()
    results = []
    for s in sessions:
        results.append({
            "id": s.id,
            "language": s.language,
            "input_text": s.input_text,
            "rules_version": s.rules_version,
            "red_flags_detected": json.loads(s.red_flags_detected) if s.red_flags_detected else [],
            "outcome": s.outcome,
            "guidance": s.guidance,
            "follow_up_questions": json.loads(s.follow_up_questions) if s.follow_up_questions else [],
            "ai_explanation": s.ai_explanation,
            "created_at": s.created_at
        })
    return results


@router.post("/evaluate", response_model=SymptomResponse)
async def evaluate_user_symptoms(
    input_in: SymptomInput,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    text_to_eval = (input_in.speech_transcript or input_in.input_text).strip()
    if not text_to_eval:
        raise HTTPException(status_code=400, detail="Symptom description cannot be empty.")

    # 1. Deterministic Rule-Based Clinical Triage (Rules Versioned)
    triage_result = evaluate_symptoms(text_to_eval)

    # 2. AI Layer (Explains and adds follow-ups, CANNOT change outcome)
    ai_enhanced = await get_triage_explanation(text_to_eval, triage_result)

    user_id = current_user.id if current_user else None
    if not user_id:
        def_p = db.query(User).filter(User.role == "patient").first()
        user_id = def_p.id if def_p else None

    # 3. Store record in database
    session_rec = SymptomSession(
        user_id=user_id,
        language=input_in.language,
        input_text=input_in.input_text,
        speech_transcript=input_in.speech_transcript,
        rules_version=RULES_VERSION,
        red_flags_detected=json.dumps(triage_result.get("red_flags", [])),
        outcome=triage_result["outcome"],  # ALWAYS rule-based outcome
        guidance=triage_result["guidance"],
        follow_up_questions=json.dumps(ai_enhanced.get("follow_up_questions", [])),
        ai_explanation=ai_enhanced.get("ai_explanation"),
        created_at=datetime.now(timezone.utc)
    )
    if user_id:
        db.add(session_rec)
        db.commit()
        db.refresh(session_rec)
        rec_id = session_rec.id
        created_at = session_rec.created_at
    else:
        rec_id = 1
        created_at = datetime.now(timezone.utc)

    return {
        "id": rec_id,
        "language": input_in.language,
        "input_text": input_in.input_text,
        "rules_version": RULES_VERSION,
        "red_flags_detected": triage_result.get("red_flags", []),
        "outcome": triage_result["outcome"],
        "guidance": triage_result["guidance"],
        "follow_up_questions": ai_enhanced.get("follow_up_questions", []),
        "ai_explanation": ai_enhanced.get("ai_explanation"),
        "created_at": created_at
    }
