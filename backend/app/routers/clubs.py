from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import re
import unicodedata

from ..db.database import get_db
from ..models.club import Club
from ..schemas.club import ClubOut
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


@router.get("/me", response_model=ClubOut)
def get_my_club(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return the club details for the authenticated user's club."""
    club = db.query(Club).filter(Club.id == current_user.club_id).first()

    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Società non trovata.",
        )

    if not club.public_code:
        club.public_code = make_unique_public_code(db, club.name, club.id)
        db.commit()
        db.refresh(club)

    return club
