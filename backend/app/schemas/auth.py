from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


class AuthMeResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    club_id: int
    email_verified: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    club_name: str = Field(min_length=2)
    username: str = Field(min_length=3)
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr