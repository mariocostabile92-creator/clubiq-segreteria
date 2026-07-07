from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import date
from pathlib import Path
from uuid import uuid4
import base64
import csv
import io

from ..db.database import get_db
from ..schemas.athlete import AthleteCreate, AthleteUpdate, AthleteOut
from ..models.athlete import Athlete
from ..models.payment import Payment
from ..models.certificate import Certificate
from ..models.club import Club
from ..core.security import get_current_user
from ..models.user import User
from ..core.storage import upload_image_to_cloudinary, validate_image_upload as validate_storage_image_upload


router = APIRouter(prefix="/athletes", tags=["athletes"])

BASE_DIR = Path(__file__).resolve().parents[3]
UPLOADS_DIR = BASE_DIR / "uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_UPLOAD_BYTES = 4 * 1024 * 1024
PLAN_ATHLETE_LIMITS = {"free": 5, "pro": 80, "premium": None}


def validate_image_upload(file: UploadFile) -> str:
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if not extension:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato immagine non supportato. Usa JPG, PNG o WEBP.")
    return extension


def public_upload_url(path: Path) -> str:
    relative = path.relative_to(UPLOADS_DIR).as_posix()
    return f"/uploads/{relative}"


def build_image_data_url(content: bytes, content_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def get_athlete_or_404(athlete_id: int, club_id: int, db: Session) -> Athlete:
    athlete = (
        db.query(Athlete)
        .filter(Athlete.id == athlete_id, Athlete.club_id == club_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Atleta non trovato"
        )

    return athlete


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


@router.post("/", response_model=AthleteOut)
def create_athlete(
    athlete_in: AthleteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ensure_can_create_athlete(current_user.club_id, db)

    athlete = Athlete(
        club_id=current_user.club_id,
        **athlete_in.dict()
    )

    db.add(athlete)
    db.commit()
    db.refresh(athlete)

    return athlete


def _clean_csv_value(row: dict, *keys: str) -> str | None:
    normalized = {str(key or "").strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(key.strip().lower())
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


@router.post("/import-csv")
async def import_athletes_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Carica un file CSV.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV non leggibile. Salvalo in UTF-8.") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV vuoto o senza intestazioni.")

    created = 0
    skipped = 0
    errors = []

    for row_number, row in enumerate(reader, start=2):
        first_name = _clean_csv_value(row, "first_name", "nome", "Nome")
        last_name = _clean_csv_value(row, "last_name", "cognome", "Cognome")
        birth_date_raw = _clean_csv_value(row, "birth_date", "data_nascita", "data nascita", "nascita")

        if not first_name or not last_name or not birth_date_raw:
            skipped += 1
            errors.append(f"Riga {row_number}: nome, cognome e data nascita sono obbligatori.")
            continue

        try:
            parsed_birth_date = date.fromisoformat(birth_date_raw)
        except ValueError:
            skipped += 1
            errors.append(f"Riga {row_number}: data nascita non valida. Usa formato YYYY-MM-DD.")
            continue

        try:
            ensure_can_create_athlete(current_user.club_id, db)
        except HTTPException:
            skipped += 1
            errors.append(f"Riga {row_number}: limite atleti del piano raggiunto.")
            break

        athlete = Athlete(
            club_id=current_user.club_id,
            first_name=first_name,
            last_name=last_name,
            birth_date=parsed_birth_date,
            group_name=_clean_csv_value(row, "group_name", "gruppo", "squadra"),
            phone=_clean_csv_value(row, "phone", "telefono_atleta", "telefono atleta"),
            email=_clean_csv_value(row, "email", "email_atleta", "email atleta"),
            parent_name_1=_clean_csv_value(row, "parent_name_1", "genitore", "nome genitore"),
            parent_phone_1=_clean_csv_value(row, "parent_phone_1", "telefono_genitore", "telefono genitore"),
            parent_email_1=_clean_csv_value(row, "parent_email_1", "email_genitore", "email genitore"),
            notes=_clean_csv_value(row, "notes", "note"),
        )
        db.add(athlete)
        created += 1

    db.commit()

    return {
        "created": created,
        "skipped": skipped,
        "errors": errors[:20],
        "expected_columns": [
            "first_name",
            "last_name",
            "birth_date",
            "group_name",
            "parent_name_1",
            "parent_phone_1",
            "parent_email_1",
        ],
    }


@router.get("/", response_model=list[AthleteOut])
def list_athletes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athletes = (
        db.query(Athlete)
        .filter(Athlete.club_id == current_user.club_id)
        .order_by(Athlete.last_name.asc(), Athlete.first_name.asc())
        .all()
    )

    return athletes


@router.get("/{athlete_id}", response_model=AthleteOut)
def get_athlete(
    athlete_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = get_athlete_or_404(
        athlete_id,
        current_user.club_id,
        db
    )

    return athlete


@router.patch("/{athlete_id}", response_model=AthleteOut)
def update_athlete(
    athlete_id: int,
    athlete_in: AthleteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = get_athlete_or_404(
        athlete_id,
        current_user.club_id,
        db
    )

    update_data = athlete_in.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(athlete, field, value)

    db.commit()
    db.refresh(athlete)

    return athlete


@router.delete("/{athlete_id}")
def delete_athlete(
    athlete_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = get_athlete_or_404(
        athlete_id,
        current_user.club_id,
        db
    )

    linked_payments = (
        db.query(Payment)
        .filter(Payment.athlete_id == athlete.id, Payment.club_id == current_user.club_id)
        .count()
    )

    linked_certificates = (
        db.query(Certificate)
        .filter(Certificate.athlete_id == athlete.id, Certificate.club_id == current_user.club_id)
        .count()
    )

    if linked_payments > 0 or linked_certificates > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Non puoi eliminare un atleta con pagamenti o certificati collegati. Elimina prima i dati collegati."
        )

    db.delete(athlete)
    db.commit()

    return {"ok": True, "message": "Atleta eliminato"}

@router.post("/{athlete_id}/photo", response_model=AthleteOut)
async def upload_athlete_photo(
    athlete_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = get_athlete_or_404(athlete_id, current_user.club_id, db)
    content = await file.read()
    validate_storage_image_upload(file.content_type, len(content))

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Immagine troppo grande. Carica un file massimo da 4 MB.")

    # Salviamo la foto come data URL nel database: resta disponibile anche dopo deploy/restart Railway.
    athlete.photo_url = upload_image_to_cloudinary(
        content,
        file.filename or "foto-atleta",
        file.content_type or "image/png",
        f"clubiq/clubs/{current_user.club_id}/athletes/{athlete.id}",
    )
    db.commit()
    db.refresh(athlete)
    return athlete
