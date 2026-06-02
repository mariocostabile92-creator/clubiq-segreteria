from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas.certificate import CertificateCreate, CertificateUpdate, CertificateOut
from ..models.certificate import Certificate
from ..models.athlete import Athlete
from ..core.security import get_current_user
from ..models.user import User


router = APIRouter(prefix="/certificates", tags=["certificates"])


def get_certificate_or_404(certificate_id: int, club_id: int, db: Session) -> Certificate:
    certificate = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.club_id == club_id)
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificato non trovato"
        )

    return certificate


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


@router.post("/", response_model=CertificateOut)
def create_certificate(
    cert_in: CertificateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ensure_athlete_belongs_to_club(
        cert_in.athlete_id,
        current_user.club_id,
        db
    )

    certificate = Certificate(
        club_id=current_user.club_id,
        **cert_in.dict()
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    return certificate


@router.get("/", response_model=list[CertificateOut])
def list_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certs = (
        db.query(Certificate)
        .filter(Certificate.club_id == current_user.club_id)
        .order_by(Certificate.expiry_date.asc(), Certificate.id.desc())
        .all()
    )

    return certs


@router.patch("/{certificate_id}", response_model=CertificateOut)
def update_certificate(
    certificate_id: int,
    cert_in: CertificateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certificate = get_certificate_or_404(certificate_id, current_user.club_id, db)

    update_data = cert_in.dict(exclude_unset=True)

    if "athlete_id" in update_data:
        ensure_athlete_belongs_to_club(
            update_data["athlete_id"],
            current_user.club_id,
            db
        )

    for field, value in update_data.items():
        setattr(certificate, field, value)

    db.commit()
    db.refresh(certificate)

    return certificate


@router.patch("/{certificate_id}/mark-valid", response_model=CertificateOut)
def mark_certificate_as_valid(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certificate = get_certificate_or_404(certificate_id, current_user.club_id, db)

    certificate.status = "valid"

    db.commit()
    db.refresh(certificate)

    return certificate


@router.delete("/{certificate_id}")
def delete_certificate(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certificate = get_certificate_or_404(certificate_id, current_user.club_id, db)

    db.delete(certificate)
    db.commit()

    return {"ok": True, "message": "Certificato eliminato"}