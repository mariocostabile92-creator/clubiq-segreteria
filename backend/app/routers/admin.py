from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
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
ALLOWED_PLANS = {"free", "pro", "premium"}
ALLOWED_STATUSES = {"active", "suspended"}


class ClubPlanUpdate(BaseModel):
    plan: str = "free"
    subscription_status: str = "active"
    admin_notes: str | None = None


def require_admin(current_user: User = Depends(get_current_user)):
    role = (current_user.role or "").lower().strip()
    if role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Accesso admin non autorizzato")
    return current_user


def club_plan_value(club: Club):
    return getattr(club, "plan", None) or "free"


def club_subscription_status_value(club: Club):
    return getattr(club, "subscription_status", None) or "active"


def club_admin_notes_value(club: Club):
    return getattr(club, "admin_notes", None) or ""


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
        "pro_clubs_count": db.query(Club).filter(getattr(Club, "plan") == "pro").count() if hasattr(Club, "plan") else 0,
        "premium_clubs_count": db.query(Club).filter(getattr(Club, "plan") == "premium").count() if hasattr(Club, "plan") else 0,
        "suspended_clubs_count": db.query(Club).filter(getattr(Club, "subscription_status") == "suspended").count() if hasattr(Club, "subscription_status") else 0,
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
            "plan": club_plan_value(user.club) if user.club else "free",
            "subscription_status": club_subscription_status_value(user.club) if user.club else "active",
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
            "plan": club_plan_value(club),
            "subscription_status": club_subscription_status_value(club),
            "admin_notes": club_admin_notes_value(club),
        })

    return rows


@router.patch("/clubs/{club_id}/plan")
def update_club_plan(
    club_id: int,
    payload: ClubPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    plan = (payload.plan or "free").lower().strip()
    status = (payload.subscription_status or "active").lower().strip()

    if plan not in ALLOWED_PLANS:
        raise HTTPException(status_code=400, detail="Piano non valido")

    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Stato cliente non valido")

    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Società non trovata")

    club.plan = plan
    club.subscription_status = status
    club.admin_notes = (payload.admin_notes or "").strip() or None

    db.commit()
    db.refresh(club)

    return {
        "id": club.id,
        "name": club.name,
        "plan": club_plan_value(club),
        "subscription_status": club_subscription_status_value(club),
        "admin_notes": club_admin_notes_value(club),
        "message": "Piano società aggiornato correttamente",
    }
