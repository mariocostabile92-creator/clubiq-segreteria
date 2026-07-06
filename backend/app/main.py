from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .core.config import settings
from .db.database import engine, Base

from .routers import auth, clubs, athletes, payments, certificates, dashboard
from .routers.admin import router as admin_router
from .routers.billing import router as billing_router
from .routers.parent_requests import router as parent_requests_router
from .routers.public_parent_requests import router as public_parent_requests_router

from .models.club import Club
from .models.user import User
from .models.athlete import Athlete
from .models.payment import Payment
from .models.certificate import Certificate
from .models.parent_request import ParentRequest
from .models.communication import Communication
from .models.audit_log import AuditLog
from .schemas.communication import CommunicationCreate, CommunicationOut
from .schemas.user_management import StaffUserCreate, StaffUserOut, StaffUserUpdate
from .core.security import get_current_user
from .core.security import get_password_hash
from .db.database import get_db
from .core.email import send_brevo_email
from .core.whatsapp import send_whatsapp_text


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


Base.metadata.create_all(bind=engine)


def apply_add_column_if_missing(connection, statement: str):
    marker = " ADD COLUMN IF NOT EXISTS "
    if marker not in statement:
        connection.execute(text(statement))
        return

    table_name = statement.split("ALTER TABLE ", 1)[1].split(" ", 1)[0]
    column_sql = statement.split(marker, 1)[1]
    column_name = column_sql.split(" ", 1)[0]
    existing = {column["name"] for column in inspect(connection).get_columns(table_name)}

    if column_name not in existing:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}"))


def run_safe_migrations():
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires_at TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires_at TIMESTAMP",

        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS plan VARCHAR DEFAULT 'free'",
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS subscription_status VARCHAR DEFAULT 'active'",
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS admin_notes TEXT",

        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR",
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR",

        # Billing.py legge questa colonna
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMP",

        # La lasciamo anche per compatibilità futura/precedente
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS stripe_current_period_end TIMESTAMP",
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS stripe_last_event_id VARCHAR",

        # ClubIQ V2.4 - White-label visuals
        "ALTER TABLE clubs ADD COLUMN IF NOT EXISTS logo VARCHAR",
        "ALTER TABLE athletes ADD COLUMN IF NOT EXISTS photo_url VARCHAR",
        "ALTER TABLE parent_requests ADD COLUMN IF NOT EXISTS privacy_consent BOOLEAN DEFAULT FALSE",
        "ALTER TABLE parent_requests ADD COLUMN IF NOT EXISTS data_processing_consent BOOLEAN DEFAULT FALSE",
        "ALTER TABLE communications ADD COLUMN IF NOT EXISTS recipient_email VARCHAR",
        "ALTER TABLE communications ADD COLUMN IF NOT EXISTS subject VARCHAR",
    ]

    with engine.begin() as connection:
        for statement in statements:
            apply_add_column_if_missing(connection, statement)


run_safe_migrations()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://*.up.railway.app",
    ],
    allow_origin_regex=r"https://.*\.up\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)
app.include_router(clubs)
app.include_router(athletes)
app.include_router(payments)
app.include_router(certificates)
app.include_router(dashboard)
app.include_router(admin_router)
app.include_router(billing_router)
app.include_router(parent_requests_router)
app.include_router(public_parent_requests_router)


CLUB_ADMIN_ROLES = {"owner", "secretary"}
ALLOWED_CLUB_ROLES = {"secretary", "coach", "president", "viewer"}


def require_club_admin(current_user: User = Depends(get_current_user)) -> User:
    if (current_user.role or "").lower() not in CLUB_ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permesso insufficiente.")
    return current_user


@app.get("/users/", response_model=list[StaffUserOut])
def list_staff_users(
    current_user: User = Depends(require_club_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(User)
        .filter(User.club_id == current_user.club_id)
        .order_by(User.id.asc())
        .all()
    )


@app.post("/users/", response_model=StaffUserOut)
def create_staff_user(
    payload: StaffUserCreate,
    current_user: User = Depends(require_club_admin),
    db: Session = Depends(get_db),
):
    role = payload.role.lower().strip()
    if role not in ALLOWED_CLUB_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ruolo non valido.")

    username = payload.username.strip()
    email = str(payload.email).strip().lower()
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username o email gia in uso.")

    user = User(
        club_id=current_user.club_id,
        username=username,
        email=email,
        hashed_password=get_password_hash(payload.password),
        role=role,
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}", response_model=StaffUserOut)
def update_staff_user(
    user_id: int,
    payload: StaffUserUpdate,
    current_user: User = Depends(require_club_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id, User.club_id == current_user.club_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato.")
    if user.role == "owner" and user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non puoi modificare un owner.")

    data = payload.model_dump(exclude_unset=True)
    if "role" in data and data["role"] is not None and user.role != "owner":
        role = data["role"].lower().strip()
        if role not in ALLOWED_CLUB_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ruolo non valido.")
        user.role = role
    if "email" in data and data["email"] is not None:
        user.email = str(data["email"]).strip().lower()
    if "is_active" in data and data["is_active"] is not None:
        user.is_active = bool(data["is_active"])
    if "password" in data and data["password"]:
        user.hashed_password = get_password_hash(data["password"])

    db.commit()
    db.refresh(user)
    return user


@app.get("/communications/", response_model=list[CommunicationOut])
def list_communications(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Communication)
        .filter(Communication.club_id == current_user.club_id)
        .order_by(Communication.created_at.desc(), Communication.id.desc())
        .limit(limit)
        .all()
    )


@app.post("/communications/", response_model=CommunicationOut)
def create_communication(
    communication_in: CommunicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_channels = {"whatsapp", "email", "phone", "note"}
    allowed_directions = {"outbound", "inbound", "internal"}
    allowed_statuses = {"opened", "sent", "draft", "failed", "logged"}

    channel = communication_in.channel.lower().strip()
    direction = communication_in.direction.lower().strip()
    status_value = communication_in.status.lower().strip()

    if channel not in allowed_channels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Canale comunicazione non valido.")
    if direction not in allowed_directions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Direzione comunicazione non valida.")
    if status_value not in allowed_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stato comunicazione non valido.")

    communication = Communication(
        club_id=current_user.club_id,
        user_id=current_user.id,
        channel=channel,
        type=communication_in.type.strip() or "WhatsApp",
        recipient=communication_in.recipient.strip() or "Contatto",
        recipient_email=(communication_in.recipient_email or "").strip() or None,
        subject=(communication_in.subject or "").strip() or None,
        phone=(communication_in.phone or "").strip() or None,
        athlete=(communication_in.athlete or "").strip() or None,
        message=communication_in.message.strip(),
        direction=direction,
        status=status_value,
    )

    if channel == "email":
        try:
            send_brevo_email(
                communication_in.recipient_email or communication_in.recipient,
                communication_in.subject or communication_in.type,
                communication_in.message,
            )
            communication.status = "sent"
        except Exception as exc:
            communication.status = "failed"
            communication.message = f"{communication.message}\n\n[Errore invio email: {exc}]"

    if channel == "whatsapp" and communication_in.send_now:
        try:
            send_whatsapp_text(communication.phone or "", communication.message)
            communication.status = "sent"
        except Exception as exc:
            communication.status = "failed"
            communication.message = f"{communication.message}\n\n[Errore invio WhatsApp: {exc}]"

    db.add(communication)
    db.commit()
    db.refresh(communication)
    return communication


@app.delete("/communications/")
def clear_communications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(Communication)
        .filter(Communication.club_id == current_user.club_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"ok": True, "deleted": deleted}


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": f"Benvenuto in {settings.APP_NAME} API"}


@app.get("/dashboard.html")
async def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/admin.html")
async def serve_admin():
    return FileResponse(FRONTEND_DIR / "admin.html")


@app.get("/iscrizione.html")
async def serve_iscrizione():
    return FileResponse(FRONTEND_DIR / "iscrizione.html")


@app.get("/index.html")
async def serve_index_html():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json")


@app.get("/service-worker.js")
async def serve_service_worker():
    return FileResponse(
        FRONTEND_DIR / "service-worker.js",
        media_type="application/javascript",
    )


if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")

if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

if UPLOADS_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
