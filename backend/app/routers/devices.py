from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Device, User
from ..schemas import DeviceCreate, DeviceResponse, MessageResponse
from ..security import get_current_user

router = APIRouter(prefix="/api/v1/devices", tags=["IoT Devices"])


@router.get("", response_model=List[DeviceResponse])
def get_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Admins see all devices, users see their assigned devices
    if current_user.role == "admin":
        devices = db.query(Device).all()
    else:
        devices = db.query(Device).filter(Device.user_id == current_user.id).all()
    return devices


@router.post("", response_model=DeviceResponse)
def register_device(device_in: DeviceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.device_id == device_in.device_id).first()
    if existing:
        existing.user_id = current_user.id
        existing.name = device_in.name
        db.commit()
        db.refresh(existing)
        return existing

    device = Device(
        device_id=device_in.device_id,
        user_id=current_user.id,
        name=device_in.name,
        status="offline"
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device
