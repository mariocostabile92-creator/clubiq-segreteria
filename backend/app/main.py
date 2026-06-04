from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

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


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"


Base.metadata.create_all(bind=engine)


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
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


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