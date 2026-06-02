from pydantic import BaseModel
from datetime import date


class PaymentBase(BaseModel):
    athlete_id: int
    amount_due: float
    amount_paid: float = 0.0
    due_date: date
    status: str = "pending"
    method: str | None = None
    notes: str | None = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    athlete_id: int | None = None
    amount_due: float | None = None
    amount_paid: float | None = None
    due_date: date | None = None
    status: str | None = None
    method: str | None = None
    notes: str | None = None


class PaymentOut(PaymentBase):
    id: int
    club_id: int

    class Config:
        from_attributes = True