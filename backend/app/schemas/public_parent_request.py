"""
Public parent request schemas.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PublicParentRequestCreate(BaseModel):
    club_code: str

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


class PublicParentRequestOut(BaseModel):
    id: int
    status: str
    club_name: str
    athlete_first_name: str
    athlete_last_name: str
    requested_group: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True