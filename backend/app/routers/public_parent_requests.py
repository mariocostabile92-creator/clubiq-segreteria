"""
Public routes for parent registration requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.club import Club
from ..models.parent_request import ParentRequest
from ..schemas.public_parent_request import (
    PublicParentRequestCreate,
    PublicParentRequestOut,
)


router = APIRouter(
    prefix="/public/parent-requests",
    tags=["public-parent-requests"],
)


@router.post("/", response_model=PublicParentRequestOut)
def create_public_parent_request(
    request_in: PublicParentRequestCreate,
    db: Session = Depends(get_db),
):
    club_code = request_in.club_code.strip().upper()

    club = (
        db.query(Club)
        .filter(Club.public_code == club_code)
        .first()
    )

    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codice società non valido",
        )

    parent_request = ParentRequest(
        club_id=club.id,
        athlete_first_name=request_in.athlete_first_name.strip(),
        athlete_last_name=request_in.athlete_last_name.strip(),
        athlete_birth_date=request_in.athlete_birth_date,
        requested_group=(request_in.requested_group or "").strip() or None,
        parent_name=request_in.parent_name.strip(),
        parent_phone=(request_in.parent_phone or "").strip() or None,
        parent_email=request_in.parent_email.strip(),
        notes=(request_in.notes or "").strip() or None,
        certificate_file_url=(request_in.certificate_file_url or "").strip() or None,
        payment_receipt_url=(request_in.payment_receipt_url or "").strip() or None,
        status="pending",
    )

    db.add(parent_request)
    db.commit()
    db.refresh(parent_request)

    return PublicParentRequestOut(
        id=parent_request.id,
        status=parent_request.status,
        club_name=club.name,
        athlete_first_name=parent_request.athlete_first_name,
        athlete_last_name=parent_request.athlete_last_name,
        requested_group=parent_request.requested_group,
        created_at=parent_request.created_at,
    )