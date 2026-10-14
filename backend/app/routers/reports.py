import os
import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Report, User
from ..schemas import ReportResponse, ReportFieldVerified, MessageResponse
from ..security import get_current_user
from ..services.ai_client import mock_extract_report_data
from ..services.audit import log_audit

router = APIRouter(prefix="/api/v1/reports", tags=["Medical Diagnostic Reports"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.get("", response_model=List[ReportResponse])
def get_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.id.desc()).all()
    return reports


@router.post("/upload", response_model=ReportResponse)
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, JPG, PNG."
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit."
        )

    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest_path = UPLOAD_DIR / safe_name
    with open(dest_path, "wb") as f:
        f.write(content)

    # Simulated AI / OCR Extraction
    extracted_records = mock_extract_report_data(file.filename)

    report = Report(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(dest_path),
        file_type=file.content_type or ext,
        uploaded_at=datetime.now(timezone.utc),
        extracted_data=json.dumps(extracted_records),
        summary=f"Laboratory analysis extracted {len(extracted_records)} biochemical markers."
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    log_audit(db, "UPLOAD_REPORT", "Report", f"Uploaded report {file.filename}", user_id=current_user.id)
    return report


@router.put("/{report_id}/verify", response_model=ReportResponse)
def verify_report_data(
    report_id: int,
    verified_fields: List[ReportFieldVerified],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.extracted_data = json.dumps([f.dict() for f in verified_fields])
    db.commit()
    db.refresh(report)

    log_audit(db, "VERIFY_REPORT", "Report", f"User confirmed report fields for #{report_id}", user_id=current_user.id)
    return report
