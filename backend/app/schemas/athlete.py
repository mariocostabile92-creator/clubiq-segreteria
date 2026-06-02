from pydantic import BaseModel, EmailStr
from datetime import date


class AthleteBase(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    group_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    parent_name_1: str | None = None
    parent_phone_1: str | None = None
    parent_email_1: EmailStr | None = None
    parent_name_2: str | None = None
    parent_phone_2: str | None = None
    parent_email_2: EmailStr | None = None
    notes: str | None = None


class AthleteCreate(AthleteBase):
    pass


class AthleteUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None
    group_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    parent_name_1: str | None = None
    parent_phone_1: str | None = None
    parent_email_1: EmailStr | None = None
    parent_name_2: str | None = None
    parent_phone_2: str | None = None
    parent_email_2: EmailStr | None = None
    notes: str | None = None


class AthleteOut(AthleteBase):
    id: int
    club_id: int

    class Config:
        from_attributes = True