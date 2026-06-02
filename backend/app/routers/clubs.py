from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.club import Club
from ..schemas.club import ClubOut
from ..core.security import get_current_user
from ..models.user import User


router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("/me", response_model=ClubOut)
def get_my_club(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return the club details for the authenticated user's club.
    """
    club = db.query(Club).filter(Club.id == current_user.club_id).first()
    return club