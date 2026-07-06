from datetime import datetime

from pydantic import BaseModel, Field


class CommunicationCreate(BaseModel):
    channel: str = Field(default="whatsapp", max_length=40)
    type: str = Field(default="WhatsApp", max_length=80)
    recipient: str = Field(default="Contatto", max_length=160)
    recipient_email: str | None = Field(default=None, max_length=160)
    subject: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=60)
    athlete: str | None = Field(default=None, max_length=160)
    message: str = Field(min_length=1, max_length=4000)
    direction: str = Field(default="outbound", max_length=40)
    status: str = Field(default="opened", max_length=40)
    send_now: bool = False


class CommunicationOut(BaseModel):
    id: int
    club_id: int
    user_id: int | None = None
    channel: str
    type: str
    recipient: str
    recipient_email: str | None = None
    subject: str | None = None
    phone: str | None = None
    athlete: str | None = None
    message: str
    direction: str
    status: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True
