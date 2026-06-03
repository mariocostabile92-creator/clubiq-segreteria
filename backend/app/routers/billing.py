import os
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db.database import get_db
from ..models.user import User
from ..models.club import Club
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/billing", tags=["billing"])


def stripe_configured():
    return bool(os.getenv("STRIPE_SECRET_KEY"))


def get_public_base_url():
    return os.getenv("PUBLIC_BASE_URL", "https://web-production-691ae.up.railway.app").rstrip("/")


def get_price_id(plan: str, interval: str):
    plan = (plan or "").lower().strip()
    interval = (interval or "").lower().strip()

    mapping = {
        ("pro", "monthly"): os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID"),
        ("pro", "yearly"): os.getenv("STRIPE_PRO_YEARLY_PRICE_ID"),
        ("premium", "monthly"): os.getenv("STRIPE_PREMIUM_MONTHLY_PRICE_ID"),
        ("premium", "yearly"): os.getenv("STRIPE_PREMIUM_YEARLY_PRICE_ID"),
    }

    price_id = mapping.get((plan, interval))
    if not price_id:
        raise HTTPException(status_code=500, detail=f"Price ID Stripe non configurato per {plan} {interval}")
    return price_id


def get_club_billing_meta(db: Session, club_id: int):
    row = db.execute(text("""
        SELECT
            COALESCE(plan, 'free') AS plan,
            COALESCE(subscription_status, 'active') AS subscription_status,
            COALESCE(stripe_customer_id, '') AS stripe_customer_id,
            COALESCE(stripe_subscription_id, '') AS stripe_subscription_id,
            current_period_end
        FROM clubs
        WHERE id = :club_id
    """), {"club_id": club_id}).mappings().first()

    if not row:
        return {
            "plan": "free",
            "subscription_status": "active",
            "stripe_customer_id": "",
            "stripe_subscription_id": "",
            "current_period_end": None,
        }

    return dict(row)


def update_club_billing(db: Session, club_id: int, **values):
    allowed = {
        "plan",
        "subscription_status",
        "stripe_customer_id",
        "stripe_subscription_id",
        "current_period_end",
    }
    values = {k: v for k, v in values.items() if k in allowed}
    if not values:
        return

    set_clause = ", ".join([f"{key} = :{key}" for key in values.keys()])
    payload = dict(values)
    payload["club_id"] = club_id
    db.execute(text(f"UPDATE clubs SET {set_clause} WHERE id = :club_id"), payload)
    db.commit()


def infer_plan_from_price(price_id: str):
    if price_id in {os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID"), os.getenv("STRIPE_PRO_YEARLY_PRICE_ID")}:
        return "pro"
    if price_id in {os.getenv("STRIPE_PREMIUM_MONTHLY_PRICE_ID"), os.getenv("STRIPE_PREMIUM_YEARLY_PRICE_ID")}:
        return "premium"
    return "free"



def get_plan_limits(plan: str):
    plan = (plan or "free").lower().strip()
    if plan == "premium":
        return {
            "athletes_limit": None,
            "athletes_label": "Illimitati",
            "pdf_enabled": True,
            "csv_enabled": True,
            "whatsapp_history_enabled": True,
            "whatsapp_full_enabled": True,
            "premium_badge": True,
        }
    if plan == "pro":
        return {
            "athletes_limit": 80,
            "athletes_label": "80 atleti",
            "pdf_enabled": True,
            "csv_enabled": True,
            "whatsapp_history_enabled": True,
            "whatsapp_full_enabled": True,
            "premium_badge": False,
        }
    return {
        "athletes_limit": 5,
        "athletes_label": "5 atleti",
        "pdf_enabled": False,
        "csv_enabled": False,
        "whatsapp_history_enabled": False,
        "whatsapp_full_enabled": False,
        "premium_badge": False,
    }

def timestamp_to_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value))
    except Exception:
        return None


@router.get("/me")
def billing_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meta = get_club_billing_meta(db, current_user.club_id)
    plan = meta.get("plan") or "free"
    limits = get_plan_limits(plan)
    return {
        "plan": plan,
        "subscription_status": meta.get("subscription_status") or "active",
        "limits": limits,
        "stripe_customer_id": meta.get("stripe_customer_id") or "",
        "stripe_subscription_id": meta.get("stripe_subscription_id") or "",
        "current_period_end": meta.get("current_period_end").isoformat() if meta.get("current_period_end") else None,
        "stripe_configured": stripe_configured(),
    }


@router.post("/checkout/{plan}/{interval}")
def create_checkout_session(
    plan: str,
    interval: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = plan.lower().strip()
    interval = interval.lower().strip()

    if plan not in {"pro", "premium"}:
        raise HTTPException(status_code=400, detail="Piano non valido")
    if interval not in {"monthly", "yearly"}:
        raise HTTPException(status_code=400, detail="Durata abbonamento non valida")
    if not stripe_configured():
        raise HTTPException(status_code=500, detail="Stripe non configurato")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    price_id = get_price_id(plan, interval)
    base_url = get_public_base_url()
    club = db.query(Club).filter(Club.id == current_user.club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Società non trovata")

    meta = get_club_billing_meta(db, club.id)
    customer_id = meta.get("stripe_customer_id") or None

    if not customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=club.name,
            metadata={"club_id": str(club.id), "user_id": str(current_user.id)},
        )
        customer_id = customer.id
        update_club_billing(db, club.id, stripe_customer_id=customer_id)

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base_url}/dashboard.html?billing=success&plan={plan}&interval={interval}",
        cancel_url=f"{base_url}/dashboard.html?billing=cancel",
        metadata={"club_id": str(club.id), "plan": plan, "interval": interval},
        subscription_data={"metadata": {"club_id": str(club.id), "plan": plan, "interval": interval}},
        allow_promotion_codes=True,
    )

    return {"checkout_url": session.url}


@router.post("/portal")
def create_customer_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not stripe_configured():
        raise HTTPException(status_code=500, detail="Stripe non configurato")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    meta = get_club_billing_meta(db, current_user.club_id)
    customer_id = meta.get("stripe_customer_id")

    if not customer_id:
        raise HTTPException(status_code=400, detail="Nessun cliente Stripe associato a questa società")

    base_url = get_public_base_url()
    portal = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{base_url}/dashboard.html?billing=portal",
    )
    return {"portal_url": portal.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret non configurato")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Webhook non valido: {error}")

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        club_id = data_object.get("metadata", {}).get("club_id")
        plan = data_object.get("metadata", {}).get("plan") or "pro"
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")

        if club_id:
            update_club_billing(
                db,
                int(club_id),
                plan=plan,
                subscription_status="active",
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
            )

    if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        subscription = data_object
        club_id = subscription.get("metadata", {}).get("club_id")
        status = subscription.get("status") or "active"
        subscription_id = subscription.get("id")
        customer_id = subscription.get("customer")
        current_period_end = timestamp_to_datetime(subscription.get("current_period_end"))
        price_id = None

        try:
            price_id = subscription.get("items", {}).get("data", [])[0].get("price", {}).get("id")
        except Exception:
            price_id = None

        plan = subscription.get("metadata", {}).get("plan") or infer_plan_from_price(price_id)
        internal_status = "active" if status in {"active", "trialing"} else "suspended"

        if club_id:
            update_club_billing(
                db,
                int(club_id),
                plan=plan,
                subscription_status=internal_status,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                current_period_end=current_period_end,
            )

    if event_type == "customer.subscription.deleted":
        subscription = data_object
        club_id = subscription.get("metadata", {}).get("club_id")
        if club_id:
            update_club_billing(
                db,
                int(club_id),
                plan="free",
                subscription_status="suspended",
                stripe_subscription_id=subscription.get("id"),
            )

    if event_type == "invoice.payment_failed":
        subscription_id = data_object.get("subscription")
        if subscription_id:
            db.execute(
                text("UPDATE clubs SET subscription_status = 'suspended' WHERE stripe_subscription_id = :sid"),
                {"sid": subscription_id},
            )
            db.commit()

    if event_type == "invoice.payment_succeeded":
        subscription_id = data_object.get("subscription")
        if subscription_id:
            db.execute(
                text("UPDATE clubs SET subscription_status = 'active' WHERE stripe_subscription_id = :sid"),
                {"sid": subscription_id},
            )
            db.commit()

    return {"received": True}
