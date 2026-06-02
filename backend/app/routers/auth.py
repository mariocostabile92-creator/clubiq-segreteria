from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import re
import unicodedata

from ..db.database import get_db
from ..models.user import User
from ..models.club import Club
from ..schemas.auth import UserCreate, UserLogin, Token
from ..core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def build_public_code(club_name: str) -> str:
    """Create a clean public registration code from the club name."""
    normalized = unicodedata.normalize("NFKD", club_name or "")
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    code = re.sub(r"[^A-Za-z0-9]+", "", ascii_name).upper()
    return code[:24] or "CLUB"


def make_unique_public_code(db: Session, club_name: str) -> str:
    base_code = build_public_code(club_name)
    candidate = base_code
    counter = 2

    while db.query(Club).filter(Club.public_code == candidate).first():
        suffix = str(counter)
        candidate = f"{base_code[:24-len(suffix)]}{suffix}"
        counter += 1

    return candidate


@router.post("/signup", response_model=Token)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new club and its first admin user (owner).
    A unique public registration code is generated from the real club name.
    """
    existing_club = db.query(Club).filter(Club.name == user_in.club_name).first()
    if existing_club:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esiste già una società con questo nome.",
        )

    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username già in uso.",
        )

    public_code = make_unique_public_code(db, user_in.club_name)

    new_club = Club(
        name=user_in.club_name.strip(),
        email=user_in.email,
        public_code=public_code,
    )
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        club_id=new_club.id,
        username=user_in.username.strip(),
        email=user_in.email,
        hashed_password=hashed_password,
        role="owner",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.username, "club_id": new_club.id})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    user = db.query(User).filter(User.username == login_in.username).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o password non corretti.",
        )

    token = create_access_token({"sub": user.username, "club_id": user.club_id})
    return Token(access_token=token)
