from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from ..db.database import get_db
from ..models.user import User
from ..models.club import Club
from ..models.athlete import Athlete
from ..models.payment import Payment
from ..models.certificate import Certificate
from ..routers.auth import get_current_user
from ..core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_ROLES = {"admin", "super_admin"}
ALLOWED_PLANS = {"free", "pro", "premium"}
ALLOWED_STATUSES = {"active", "suspended"}


class ClubPlanUpdate(BaseModel):
    plan: str = "free"
    subscription_status: str = "active"
    admin_notes: str | None = None


def get_platform_admin_emails() -> set[str]:
    return {
        email.strip().lower()
        for email in (settings.PLATFORM_ADMIN_EMAILS or "").split(",")
        if email.strip()
    }


def is_platform_admin(current_user: User) -> bool:
    role = (current_user.role or "").lower().strip()
    email = (current_user.email or "").lower().strip()
    return role in ADMIN_ROLES or email in get_platform_admin_emails()


def require_admin(current_user: User = Depends(get_current_user)):
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Accesso admin non autorizzato")
    return current_user


def get_club_admin_meta(db: Session, club_id: int) -> dict:
    row = db.execute(
        text("""
            SELECT
                COALESCE(plan, 'free') AS plan,
                COALESCE(subscription_status, 'active') AS subscription_status,
                COALESCE(admin_notes, '') AS admin_notes
            FROM clubs
            WHERE id = :club_id
        """),
        {"club_id": club_id},
    ).mappings().first()

    if not row:
        return {"plan": "free", "subscription_status": "active", "admin_notes": ""}

    return {
        "plan": row.get("plan") or "free",
        "subscription_status": row.get("subscription_status") or "active",
        "admin_notes": row.get("admin_notes") or "",
    }


@router.get("/summary")
def admin_summary(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    total_due = db.query(func.coalesce(func.sum(Payment.amount_due), 0)).scalar() or 0
    total_paid = db.query(func.coalesce(func.sum(Payment.amount_paid), 0)).scalar() or 0

    pro_clubs_count = db.execute(text("SELECT COUNT(*) FROM clubs WHERE COALESCE(plan, 'free') = 'pro'")).scalar() or 0
    premium_clubs_count = db.execute(text("SELECT COUNT(*) FROM clubs WHERE COALESCE(plan, 'free') = 'premium'")).scalar() or 0
    suspended_clubs_count = db.execute(text("SELECT COUNT(*) FROM clubs WHERE COALESCE(subscription_status, 'active') = 'suspended'")).scalar() or 0

    return {
        "users_count": db.query(User).count(),
        "clubs_count": db.query(Club).count(),
        "athletes_count": db.query(Athlete).count(),
        "payments_count": db.query(Payment).count(),
        "certificates_count": db.query(Certificate).count(),
        "verified_users_count": db.query(User).filter(User.email_verified == True).count(),
        "active_users_count": db.query(User).filter(User.is_active == True).count(),
        "pro_clubs_count": int(pro_clubs_count),
        "premium_clubs_count": int(premium_clubs_count),
        "suspended_clubs_count": int(suspended_clubs_count),
        "total_due": float(total_due),
        "total_paid": float(total_paid),
        "total_residual": float(total_due) - float(total_paid),
    }


@router.get("/users")
def admin_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id.desc()).limit(500).all()
    rows = []

    for user in users:
        meta = get_club_admin_meta(db, user.club_id) if user.club_id else {"plan": "free", "subscription_status": "active"}
        rows.append({
            "id": user.id,
            "club_id": user.club_id,
            "club_name": user.club.name if user.club else "-",
            "username": user.username,
            "email": user.email,
            "role": user.role or "member",
            "is_active": bool(user.is_active),
            "email_verified": bool(user.email_verified),
            "plan": meta["plan"],
            "subscription_status": meta["subscription_status"],
        })

    return rows


@router.get("/clubs")
def admin_clubs(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    clubs = db.query(Club).order_by(Club.id.desc()).limit(500).all()
    rows = []

    for club in clubs:
        total_due = db.query(func.coalesce(func.sum(Payment.amount_due), 0)).filter(Payment.club_id == club.id).scalar() or 0
        total_paid = db.query(func.coalesce(func.sum(Payment.amount_paid), 0)).filter(Payment.club_id == club.id).scalar() or 0
        meta = get_club_admin_meta(db, club.id)

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
            "plan": meta["plan"],
            "subscription_status": meta["subscription_status"],
            "admin_notes": meta["admin_notes"],
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
    notes = (payload.admin_notes or "").strip()

    if plan not in ALLOWED_PLANS:
        raise HTTPException(status_code=400, detail="Piano non valido")

    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Stato cliente non valido")

    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Società non trovata")

    db.execute(
        text("""
            UPDATE clubs
            SET plan = :plan,
                subscription_status = :status,
                admin_notes = :notes
            WHERE id = :club_id
        """),
        {"plan": plan, "status": status, "notes": notes if notes else None, "club_id": club_id},
    )
    db.commit()

    meta = get_club_admin_meta(db, club_id)

    return {
        "id": club.id,
        "name": club.name,
        "plan": meta["plan"],
        "subscription_status": meta["subscription_status"],
        "admin_notes": meta["admin_notes"],
        "message": "Piano società aggiornato correttamente",
    }
