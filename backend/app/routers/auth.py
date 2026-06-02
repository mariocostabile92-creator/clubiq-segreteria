from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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


@router.post("/signup", response_model=Token)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new club and its first admin user (owner).

    If a club with the same name or a user with the same username exists,
    a 400 error is raised.
    """
    # Check if club name already exists
    existing_club = db.query(Club).filter(Club.name == user_in.club_name).first()
    if existing_club:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esiste già una società con questo nome.",
        )

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username già in uso.",
        )

    # Create the club
    new_club = Club(
        name=user_in.club_name,
        email=user_in.email,
    )
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    # Create the user as club owner
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        club_id=new_club.id,
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        role="owner",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    token = create_access_token({"sub": new_user.username, "club_id": new_club.id})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    """
    user = db.query(User).filter(User.username == login_in.username).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username o password non corretti.",
        )

    token = create_access_token({"sub": user.username, "club_id": user.club_id})
    return Token(access_token=token)