from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import re
import unicodedata

from ..db.database import get_db
from ..models.club import Club
from ..schemas.club import ClubOut, ClubUpdate
from ..core.security import get_current_user
from ..models.user import User


router = APIRouter(prefix="/clubs", tags=["clubs"])


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


def get_current_club_or_404(current_user: User, db: Session) -> Club:
    club = db.query(Club).filter(Club.id == current_user.club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Società non trovata.")
    return club


@router.get("/me", response_model=ClubOut)
def get_my_club(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    club = get_current_club_or_404(current_user, db)
    if not club.public_code:
        club.public_code = make_unique_public_code(db, club.name, club.id)
        db.commit()
        db.refresh(club)
    return club


@router.patch("/me", response_model=ClubOut)
def update_my_club(club_in: ClubUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    club = get_current_club_or_404(current_user, db)
    data = club_in.model_dump(exclude_unset=True)

    if "name" in data and data["name"]:
        new_name = data["name"].strip()
        existing = db.query(Club).filter(Club.name == new_name, Club.id != club.id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esiste già una società con questo nome.")
        club.name = new_name

    for field in ["email", "phone", "address", "president", "secretary", "logo"]:
        if field in data:
            value = data[field]
            setattr(club, field, value.strip() if isinstance(value, str) and value.strip() else None)

    db.commit()
    db.refresh(club)
    return club


@router.patch("/me/regenerate-code", response_model=ClubOut)
def regenerate_my_public_code(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    club = get_current_club_or_404(current_user, db)
    club.public_code = make_unique_public_code(db, club.name, club.id)
    db.commit()
    db.refresh(club)
    return club
