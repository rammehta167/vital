from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Contact, User
from ..schemas import ContactCreate, ContactUpdate, ContactResponse, MessageResponse
from ..security import get_current_user

router = APIRouter(prefix="/api/v1/contacts", tags=["Emergency Contacts"])


@router.get("", response_model=List[ContactResponse])
def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter(Contact.user_id == current_user.id).order_by(Contact.priority_order).all()
    return contacts


@router.post("", response_model=ContactResponse)
def create_contact(contact_in: ContactCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = Contact(
        user_id=current_user.id,
        name=contact_in.name,
        relationship_type=contact_in.relationship_type,
        phone=contact_in.phone,
        email=contact_in.email,
        telegram_chat_id=contact_in.telegram_chat_id,
        notify_sos=contact_in.notify_sos,
        notify_warning=contact_in.notify_warning,
        priority_order=contact_in.priority_order
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, contact_in: ContactUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, val in contact_in.dict(exclude_unset=True).items():
        setattr(contact, field, val)

    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", response_model=MessageResponse)
def delete_contact(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted successfully"}
