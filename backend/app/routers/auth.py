from datetime import datetime, timedelta
import re
import secrets
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.user import User
from ..models.club import Club
from ..schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    MessageResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from ..core.email import (
    get_app_base_url,
    send_brevo_email,
    build_verify_email_html,
    build_reset_password_html,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def build_public_code(club_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", club_name or "")
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    code = re.sub(r"[^A-Za-z0-9]+", "", ascii_name).upper()
    return code[:24] or "CLUB"


def make_unique_public_code(db: Session, club_name: str, current_club_id: int | None = None) -> str:
    base_code = build_public_code(club_name)
    candidate = base_code
    counter = 2

    while True:
        existing = db.query(Club).filter(Club.public_code == candidate).first()
        if not existing or existing.id == current_club_id:
            return candidate

        suffix = str(counter)
        candidate = f"{base_code[:24-len(suffix)]}{suffix}"
        counter += 1


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def send_verification_email(user: User) -> None:
    base_url = get_app_base_url()
    if not base_url:
        raise RuntimeError("APP_BASE_URL non configurato.")

    verify_link = f"{base_url}/index.html?verify_token={user.email_verification_token}"
    send_brevo_email(
        user.email,
        "Verifica la tua email - ClubIQ Segreteria",
        build_verify_email_html(verify_link),
    )


@router.post("/signup", response_model=Token)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_club = db.query(Club).filter(Club.name == user_in.club_name).first()
    if existing_club:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esiste già una società con questo nome.")

    existing_user = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username o email già in uso.")

    public_code = make_unique_public_code(db, user_in.club_name)
    new_club = Club(name=user_in.club_name.strip(), email=user_in.email, public_code=public_code)
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    verification_token = generate_token()
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        club_id=new_club.id,
        username=user_in.username.strip(),
        email=user_in.email,
        hashed_password=hashed_password,
        role="owner",
        email_verified=False,
        email_verification_token=verification_token,
        email_verification_expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        send_verification_email(new_user)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Società creata, ma invio email verifica non riuscito: {exc}")

    token = create_access_token({"sub": new_user.username, "club_id": new_club.id})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == login_in.username) | (User.email == login_in.username)).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username/email o password non corretti.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disattivato.")

    token = create_access_token({"sub": user.username, "club_id": user.club_id})
    return Token(access_token=token)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    generic_message = "Se l'email è registrata, riceverai un link per reimpostare la password."
    if not user:
        return MessageResponse(message=generic_message)

    user.password_reset_token = generate_token()
    user.password_reset_expires_at = datetime.utcnow() + timedelta(minutes=60)
    db.commit()
    db.refresh(user)

    base_url = get_app_base_url()
    if not base_url:
        raise HTTPException(status_code=500, detail="APP_BASE_URL non configurato.")

    reset_link = f"{base_url}/index.html?reset_token={user.password_reset_token}"

    try:
        send_brevo_email(
            user.email,
            "Reimposta la password - ClubIQ Segreteria",
            build_reset_password_html(reset_link),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invio email reset non riuscito: {exc}")

    return MessageResponse(message=generic_message)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == payload.token).first()
    if not user or not user.password_reset_expires_at or user.password_reset_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Link reset password non valido o scaduto.")

    user.hashed_password = get_password_hash(payload.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()

    return MessageResponse(message="Password aggiornata correttamente. Ora puoi accedere.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == payload.token).first()
    if not user or not user.email_verification_expires_at or user.email_verification_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Link verifica email non valido o scaduto.")

    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_expires_at = None
    db.commit()

    return MessageResponse(message="Email verificata correttamente.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    generic_message = "Se l'email è registrata e non ancora verificata, riceverai un nuovo link di verifica."

    if not user or user.email_verified:
        return MessageResponse(message=generic_message)

    user.email_verification_token = generate_token()
    user.email_verification_expires_at = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    db.refresh(user)

    try:
        send_verification_email(user)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invio email verifica non riuscito: {exc}")

    return MessageResponse(message=generic_message)
