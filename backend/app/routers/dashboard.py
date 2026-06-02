from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from ..db.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.athlete import Athlete
from ..models.payment import Payment
from ..models.certificate import Certificate


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Provide a summary of key statistics for the current user's club.

    Returns counts of athletes, outstanding amounts, overdue payments, and
    certificate statuses.
    """
    club_id = current_user.club_id

    # Count athletes
    athletes_count = db.query(Athlete).filter(Athlete.club_id == club_id).count()

    # Aggregate payment data
    payments = db.query(Payment).filter(Payment.club_id == club_id).all()
    total_residuo = 0.0
    quote_scadute = 0
    today = date.today()
    for p in payments:
        residuo = (p.amount_due or 0.0) - (p.amount_paid or 0.0)
        total_residuo += residuo
        if residuo > 0 and p.due_date and p.due_date < today:
            quote_scadute += 1

    # Certificate status counts
    certs = db.query(Certificate).filter(Certificate.club_id == club_id).all()
    certificati_scaduti = 0
    certificati_in_scadenza = 0
    for c in certs:
        if c.expiry_date and c.expiry_date < today:
            certificati_scaduti += 1
        elif c.expiry_date and (c.expiry_date - today).days <= 30:
            certificati_in_scadenza += 1

    return {
        "athletes_count": athletes_count,
        "total_residuo": total_residuo,
        "quote_scadute": quote_scadute,
        "certificati_scaduti": certificati_scaduti,
        "certificati_in_scadenza": certificati_in_scadenza,
    }