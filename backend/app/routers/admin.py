from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.database import get_db
from ..models.user import User
from ..models.club import Club
from ..models.athlete import Athlete
from ..models.payment import Payment
from ..models.certificate import Certificate
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_ROLES = {"admin", "owner"}


def require_admin(current_user: User = Depends(get_current_user)):
    role = (current_user.role or "").lower()
    if role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Accesso admin non autorizzato")
    return current_user


@router.get("/summary")
def admin_summary(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    total_due = db.query(func.coalesce(func.sum(Payment.amount_due), 0)).scalar() or 0
    total_paid = db.query(func.coalesce(func.sum(Payment.amount_paid), 0)).scalar() or 0

    return {
        "users_count": db.query(User).count(),
        "clubs_count": db.query(Club).count(),
        "athletes_count": db.query(Athlete).count(),
        "payments_count": db.query(Payment).count(),
        "certificates_count": db.query(Certificate).count(),
        "verified_users_count": db.query(User).filter(User.email_verified == True).count(),
        "active_users_count": db.query(User).filter(User.is_active == True).count(),
        "total_due": float(total_due),
        "total_paid": float(total_paid),
        "total_residual": float(total_due) - float(total_paid),
    }


@router.get("/users")
def admin_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id.desc()).limit(500).all()
    return [
        {
            "id": user.id,
            "club_id": user.club_id,
            "club_name": user.club.name if user.club else "-",
            "username": user.username,
            "email": user.email,
            "role": user.role or "member",
            "is_active": bool(user.is_active),
            "email_verified": bool(user.email_verified),
            "plan": "free",
        }
        for user in users
    ]


@router.get("/clubs")
def admin_clubs(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    clubs = db.query(Club).order_by(Club.id.desc()).limit(500).all()
    rows = []

    for club in clubs:
        total_due = db.query(func.coalesce(func.sum(Payment.amount_due), 0)).filter(Payment.club_id == club.id).scalar() or 0
        total_paid = db.query(func.coalesce(func.sum(Payment.amount_paid), 0)).filter(Payment.club_id == club.id).scalar() or 0

        rows.append({
            "id": club.id,
            "name": club.name,
            "public_code": club.public_code,
            "email": club.email,
            "phone": club.phone,
            "created_at": club.created_at.isoformat() if club.created_at else None,
            "users_count": db.query(User).filter(User.club_id == club.id).count(),
            "athletes_count": db.query(Athlete).filter(Athlete.club_id == club.id).count(),
            "payments_count": db.query(Payment).filter(Payment.club_id == club.id).count(),
            "certificates_count": db.query(Certificate).filter(Certificate.club_id == club.id).count(),
            "total_due": float(total_due),
            "total_paid": float(total_paid),
            "total_residual": float(total_due) - float(total_paid),
            "plan": "free",
        })

    return rows
