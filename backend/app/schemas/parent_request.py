"""
Pydantic schemas for parent registration requests.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ParentRequestCreate(BaseModel):
    athlete_first_name: str
    athlete_last_name: str
    athlete_birth_date: date
    requested_group: Optional[str] = None

    parent_name: str
    parent_phone: Optional[str] = None
    parent_email: EmailStr

    notes: Optional[str] = None
    certificate_file_url: Optional[str] = None
    payment_receipt_url: Optional[str] = None


class ParentRequestUpdate(BaseModel):
    athlete_first_name: Optional[str] = None
    athlete_last_name: Optional[str] = None
    athlete_birth_date: Optional[date] = None
    requested_group: Optional[str] = None

    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[EmailStr] = None

    notes: Optional[str] = None
    certificate_file_url: Optional[str] = None
    payment_receipt_url: Optional[str] = None

    status: Optional[str] = None
    review_note: Optional[str] = None


class ParentRequestReject(BaseModel):
    review_note: Optional[str] = None


class ParentRequestOut(BaseModel):
    id: int
    club_id: int

    athlete_first_name: str
    athlete_last_name: str
    athlete_birth_date: date
    requested_group: Optional[str] = None

    parent_name: str
    parent_phone: Optional[str] = None
    parent_email: EmailStr

    notes: Optional[str] = None
    certificate_file_url: Optional[str] = None
    payment_receipt_url: Optional[str] = None

    status: str
    review_note: Optional[str] = None
    created_athlete_id: Optional[int] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True