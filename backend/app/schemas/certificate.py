from pydantic import BaseModel
from datetime import date


class CertificateBase(BaseModel):
    athlete_id: int
    type: str
    issue_date: date
    expiry_date: date
    status: str = "valid"
    file_path: str | None = None


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(BaseModel):
    athlete_id: int | None = None
    type: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    status: str | None = None
    file_path: str | None = None


class CertificateOut(CertificateBase):
    id: int
    club_id: int

    class Config:
        from_attributes = True