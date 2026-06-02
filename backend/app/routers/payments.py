from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas.payment import PaymentCreate, PaymentUpdate, PaymentOut
from ..models.payment import Payment
from ..models.athlete import Athlete
from ..core.security import get_current_user
from ..models.user import User


router = APIRouter(prefix="/payments", tags=["payments"])


def get_payment_or_404(payment_id: int, club_id: int, db: Session) -> Payment:
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.club_id == club_id)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento non trovato"
        )

    return payment


def ensure_athlete_belongs_to_club(athlete_id: int, club_id: int, db: Session) -> None:
    athlete = (
        db.query(Athlete)
        .filter(Athlete.id == athlete_id, Athlete.club_id == club_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Atleta non valido per questa società"
        )


@router.post("/", response_model=PaymentOut)
def create_payment(
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ensure_athlete_belongs_to_club(
        payment_in.athlete_id,
        current_user.club_id,
        db
    )

    payment = Payment(
        club_id=current_user.club_id,
        **payment_in.dict()
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


@router.get("/", response_model=list[PaymentOut])
def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payments = (
        db.query(Payment)
        .filter(Payment.club_id == current_user.club_id)
        .order_by(Payment.due_date.desc(), Payment.id.desc())
        .all()
    )

    return payments


@router.patch("/{payment_id}", response_model=PaymentOut)
def update_payment(
    payment_id: int,
    payment_in: PaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = get_payment_or_404(payment_id, current_user.club_id, db)

    update_data = payment_in.dict(exclude_unset=True)

    if "athlete_id" in update_data:
        ensure_athlete_belongs_to_club(
            update_data["athlete_id"],
            current_user.club_id,
            db
        )

    for field, value in update_data.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)

    return payment


@router.patch("/{payment_id}/mark-paid", response_model=PaymentOut)
def mark_payment_as_paid(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = get_payment_or_404(payment_id, current_user.club_id, db)

    payment.amount_paid = payment.amount_due
    payment.status = "paid"

    db.commit()
    db.refresh(payment)

    return payment


@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = get_payment_or_404(payment_id, current_user.club_id, db)

    db.delete(payment)
    db.commit()

    return {"ok": True, "message": "Pagamento eliminato"}