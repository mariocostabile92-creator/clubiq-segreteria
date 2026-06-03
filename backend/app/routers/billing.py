import os
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.user import User
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_PREMIUM_PRICE_ID = os.getenv("STRIPE_PREMIUM_PRICE_ID", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://web-production-691ae.up.railway.app").rstrip("/")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

PLAN_BY_PRICE = {
    STRIPE_PRO_PRICE_ID: "pro",
    STRIPE_PREMIUM_PRICE_ID: "premium",
}


def require_stripe_config():
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY non configurata")
    if not STRIPE_PRO_PRICE_ID or not STRIPE_PREMIUM_PRICE_ID:
        raise HTTPException(status_code=500, detail="Price ID Stripe non configurati")


def get_billing_meta(db: Session, club_id: int) -> dict:
    row = db.execute(text("""
        SELECT
            id,
            name,
            email,
            COALESCE(plan, 'free') AS plan,
            COALESCE(subscription_status, 'active') AS subscription_status,
            stripe_customer_id,
            stripe_subscription_id,
            stripe_current_period_end
        FROM clubs
        WHERE id = :club_id
    """), {"club_id": club_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Società non trovata")

    period_end = row.get("stripe_current_period_end")
    return {
        "club_id": row.get("id"),
        "club_name": row.get("name"),
        "club_email": row.get("email"),
        "plan": row.get("plan") or "free",
        "subscription_status": row.get("subscription_status") or "active",
        "stripe_customer_id": row.get("stripe_customer_id"),
        "stripe_subscription_id": row.get("stripe_subscription_id"),
        "stripe_current_period_end": period_end.isoformat() if hasattr(period_end, "isoformat") else period_end,
    }


def update_club_billing(db: Session, club_id: int, **values):
    allowed = {
        "plan", "subscription_status", "stripe_customer_id",
        "stripe_subscription_id", "stripe_current_period_end", "stripe_last_event_id"
    }
    data = {k: v for k, v in values.items() if k in allowed}
    if not data:
        return
    set_sql = ", ".join([f"{key} = :{key}" for key in data.keys()])
    data["club_id"] = club_id
    db.execute(text(f"UPDATE clubs SET {set_sql} WHERE id = :club_id"), data)
    db.commit()


def get_or_create_customer(db: Session, current_user: User, club: dict) -> str:
    if club.get("stripe_customer_id"):
        return club["stripe_customer_id"]

    customer = stripe.Customer.create(
        email=current_user.email,
        name=club.get("club_name") or current_user.username,
        metadata={
            "club_id": str(current_user.club_id),
            "user_id": str(current_user.id),
            "source": "clubiq",
        },
    )
    update_club_billing(db, current_user.club_id, stripe_customer_id=customer.id)
    return customer.id


@router.get("/me")
def billing_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_billing_meta(db, current_user.club_id)


@router.post("/checkout/{plan}")
def create_checkout_session(plan: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_stripe_config()
    plan = (plan or "").lower().strip()
    if plan not in {"pro", "premium"}:
        raise HTTPException(status_code=400, detail="Piano non valido")

    price_id = STRIPE_PRO_PRICE_ID if plan == "pro" else STRIPE_PREMIUM_PRICE_ID
    club = get_billing_meta(db, current_user.club_id)
    customer_id = get_or_create_customer(db, current_user, club)

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{PUBLIC_BASE_URL}/dashboard.html?billing=success",
        cancel_url=f"{PUBLIC_BASE_URL}/dashboard.html?billing=cancel",
        metadata={"club_id": str(current_user.club_id), "plan": plan},
        subscription_data={"metadata": {"club_id": str(current_user.club_id), "plan": plan}},
        allow_promotion_codes=True,
    )
    return {"url": session.url}


@router.post("/portal")
def create_customer_portal(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_stripe_config()
    club = get_billing_meta(db, current_user.club_id)
    customer_id = club.get("stripe_customer_id")
    if not customer_id:
        customer_id = get_or_create_customer(db, current_user, club)

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{PUBLIC_BASE_URL}/dashboard.html?billing=portal",
    )
    return {"url": session.url}


def find_club_id_for_customer_or_subscription(db: Session, customer_id=None, subscription_id=None):
    if subscription_id:
        row = db.execute(text("SELECT id FROM clubs WHERE stripe_subscription_id = :sid"), {"sid": subscription_id}).first()
        if row:
            return row[0]
    if customer_id:
        row = db.execute(text("SELECT id FROM clubs WHERE stripe_customer_id = :cid"), {"cid": customer_id}).first()
        if row:
            return row[0]
    return None


def datetime_from_ts(value):
    if not value:
        return None
    return datetime.utcfromtimestamp(int(value))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET non configurato")

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Webhook Stripe non valido: {exc}")

    event_id = event.get("id")
    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        club_id = obj.get("metadata", {}).get("club_id")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        plan = obj.get("metadata", {}).get("plan") or "pro"
        if club_id:
            update_club_billing(
                db, int(club_id), plan=plan, subscription_status="active",
                stripe_customer_id=customer_id, stripe_subscription_id=subscription_id,
                stripe_last_event_id=event_id,
            )

    elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        customer_id = obj.get("customer")
        subscription_id = obj.get("id")
        status = obj.get("status") or "active"
        price_id = None
        items = obj.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
        plan = PLAN_BY_PRICE.get(price_id, "pro")
        club_id = obj.get("metadata", {}).get("club_id") or find_club_id_for_customer_or_subscription(db, customer_id, subscription_id)
        mapped_status = "active" if status in {"active", "trialing"} else "suspended"
        if club_id:
            update_club_billing(
                db, int(club_id), plan=plan, subscription_status=mapped_status,
                stripe_customer_id=customer_id, stripe_subscription_id=subscription_id,
                stripe_current_period_end=datetime_from_ts(obj.get("current_period_end")),
                stripe_last_event_id=event_id,
            )

    elif event_type == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        subscription_id = obj.get("id")
        club_id = obj.get("metadata", {}).get("club_id") or find_club_id_for_customer_or_subscription(db, customer_id, subscription_id)
        if club_id:
            update_club_billing(
                db, int(club_id), plan="free", subscription_status="suspended",
                stripe_subscription_id=subscription_id, stripe_last_event_id=event_id,
            )

    elif event_type in {"invoice.payment_failed", "customer.subscription.paused"}:
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription") or obj.get("id")
        club_id = find_club_id_for_customer_or_subscription(db, customer_id, subscription_id)
        if club_id:
            update_club_billing(db, int(club_id), subscription_status="suspended", stripe_last_event_id=event_id)

    elif event_type == "invoice.payment_succeeded":
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        club_id = find_club_id_for_customer_or_subscription(db, customer_id, subscription_id)
        if club_id:
            update_club_billing(db, int(club_id), subscription_status="active", stripe_last_event_id=event_id)

    return JSONResponse({"received": True})
