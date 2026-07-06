"""
Admin routes for parent registration requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.athlete import Athlete
from ..models.club import Club
from ..models.parent_request import ParentRequest
from ..schemas.parent_request import (
    ParentRequestCreate,
    ParentRequestUpdate,
    ParentRequestReject,
    ParentRequestOut,
)


router = APIRouter(
    prefix="/parent-requests",
    tags=["parent-requests"],
)

PLAN_ATHLETE_LIMITS = {"free": 5, "pro": 80, "premium": None}


def get_parent_request_or_404(
    request_id: int,
    club_id: int,
    db: Session,
) -> ParentRequest:
    parent_request = (
        db.query(ParentRequest)
        .filter(
            ParentRequest.id == request_id,
            ParentRequest.club_id == club_id,
        )
        .first()
    )

    if not parent_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Richiesta non trovata",
        )

    return parent_request


def ensure_can_create_athlete(club_id: int, db: Session) -> None:
    club = db.query(Club).filter(Club.id == club_id).first()
    plan = ((getattr(club, "plan", None) or "free").strip().lower())
    limit = PLAN_ATHLETE_LIMITS.get(plan, PLAN_ATHLETE_LIMITS["free"])

    if limit is None:
        return

    athletes_count = db.query(Athlete).filter(Athlete.club_id == club_id).count()
    if athletes_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite piano raggiunto: il piano {plan} consente fino a {limit} atleti.",
        )


@router.post("/", response_model=ParentRequestOut)
def create_parent_request(
    request_in: ParentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent_request = ParentRequest(
        club_id=current_user.club_id,
        status="pending",
        **request_in.dict(),
    )

    db.add(parent_request)
    db.commit()
    db.refresh(parent_request)

    return parent_request


@router.get("/", response_model=list[ParentRequestOut])
def list_parent_requests(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ParentRequest).filter(
        ParentRequest.club_id == current_user.club_id
    )

    if status_filter:
        query = query.filter(ParentRequest.status == status_filter)

    return (
        query
        .order_by(ParentRequest.created_at.desc(), ParentRequest.id.desc())
        .all()
    )


@router.get("/{request_id}", response_model=ParentRequestOut)
def get_parent_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_parent_request_or_404(
        request_id=request_id,
        club_id=current_user.club_id,
        db=db,
    )


@router.patch("/{request_id}", response_model=ParentRequestOut)
def update_parent_request(
    request_id: int,
    request_in: ParentRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent_request = get_parent_request_or_404(
        request_id=request_id,
        club_id=current_user.club_id,
        db=db,
    )

    update_data = request_in.dict(exclude_unset=True)
    allowed_statuses = {"pending", "approved", "rejected"}

    if "status" in update_data and update_data["status"] not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stato richiesta non valido",
        )

    for field, value in update_data.items():
        setattr(parent_request, field, value)

    db.commit()
    db.refresh(parent_request)

    return parent_request


@router.patch("/{request_id}/approve", response_model=ParentRequestOut)
def approve_parent_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent_request = get_parent_request_or_404(
        request_id=request_id,
        club_id=current_user.club_id,
        db=db,
    )

    if parent_request.status == "approved" and parent_request.created_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questa richiesta è già stata approvata",
        )

    ensure_can_create_athlete(current_user.club_id, db)

    athlete = Athlete(
        club_id=current_user.club_id,
        first_name=parent_request.athlete_first_name,
        last_name=parent_request.athlete_last_name,
        birth_date=parent_request.athlete_birth_date,
        group_name=parent_request.requested_group,
        phone=None,
        email=None,
        parent_name_1=parent_request.parent_name,
        parent_phone_1=parent_request.parent_phone,
        parent_email_1=parent_request.parent_email,
        parent_name_2=None,
        parent_phone_2=None,
        parent_email_2=None,
        notes=parent_request.notes,
    )

    db.add(athlete)
    db.flush()

    parent_request.status = "approved"
    parent_request.created_athlete_id = athlete.id
    parent_request.review_note = "Richiesta approvata e atleta creato."

    db.commit()
    db.refresh(parent_request)

    return parent_request


@router.patch("/{request_id}/reject", response_model=ParentRequestOut)
def reject_parent_request(
    request_id: int,
    reject_in: ParentRequestReject,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent_request = get_parent_request_or_404(
        request_id=request_id,
        club_id=current_user.club_id,
        db=db,
    )

    if parent_request.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non puoi rifiutare una richiesta già approvata",
        )

    parent_request.status = "rejected"
    parent_request.review_note = reject_in.review_note or "Richiesta rifiutata."

    db.commit()
    db.refresh(parent_request)

    return parent_request


@router.delete("/{request_id}")
def delete_parent_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    parent_request = get_parent_request_or_404(
        request_id=request_id,
        club_id=current_user.club_id,
        db=db,
    )

    if parent_request.status == "approved" and parent_request.created_athlete_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non puoi eliminare una richiesta già approvata con atleta creato",
        )

    db.delete(parent_request)
    db.commit()

    return {"ok": True, "message": "Richiesta eliminata"}
