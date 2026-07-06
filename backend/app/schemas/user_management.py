from pydantic import BaseModel, EmailStr, Field


class StaffUserCreate(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "secretary"


class StaffUserUpdate(BaseModel):
    email: EmailStr | None = None
    role: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class StaffUserOut(BaseModel):
    id: int
    club_id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    email_verified: bool

    class Config:
        from_attributes = True
