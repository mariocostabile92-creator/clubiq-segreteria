"""
Public routes for parent registration requests.
Upload documenti V1 - Cloudinary.
"""

import base64
import os
import time
import uuid
from urllib import parse, request as urlrequest

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.club import Club
from ..models.parent_request import ParentRequest
from ..schemas.public_parent_request import (
    PublicParentRequestCreate,
    PublicParentRequestOut,
)
from ..services.audit import create_audit_log


router = APIRouter(
    prefix="/public/parent-requests",
    tags=["public-parent-requests"],
)

ALLOWED_UPLOAD_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_UPLOAD_SIZE = 8 * 1024 * 1024


def _cloudinary_config():
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()

    if not cloud_name or not api_key or not api_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload documenti non configurato. Mancano variabili Cloudinary.",
        )

    return cloud_name, api_key, api_secret


def _upload_to_cloudinary(file_bytes: bytes, filename: str, content_type: str, document_type: str) -> str:
    cloud_name, api_key, api_secret = _cloudinary_config()

    if content_type not in ALLOWED_UPLOAD_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato file non valido. Carica PDF, JPG, PNG o WEBP.",
        )

    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File troppo grande. Dimensione massima: 8 MB.",
        )

    resource_type = "raw" if content_type == "application/pdf" else "image"
    timestamp = str(int(time.time()))
    safe_name = "".join(ch for ch in (filename or "documento").rsplit(".", 1)[0] if ch.isalnum() or ch in ("-", "_")) or "documento"
    public_id = f"clubiq/parent-requests/{document_type}/{uuid.uuid4().hex}_{safe_name}"

    # Signature Cloudinary: sha1 dei parametri firmati ordinati + api_secret.
    import hashlib
    params_to_sign = f"folder=clubiq/parent-requests/{document_type}&public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()

    data_uri = f"data:{content_type};base64,{base64.b64encode(file_bytes).decode('utf-8')}"
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/{resource_type}/upload"

    payload = parse.urlencode({
        "file": data_uri,
        "api_key": api_key,
        "timestamp": timestamp,
        "signature": signature,
        "folder": f"clubiq/parent-requests/{document_type}",
        "public_id": public_id,
    }).encode("utf-8")

    req = urlrequest.Request(upload_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            import json
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Errore durante il caricamento del documento.",
        ) from exc

    secure_url = result.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upload completato senza URL documento.",
        )

    return secure_url


@router.post("/upload-document")
async def upload_parent_document(
    document_type: str,
    file: UploadFile = File(...),
):
    normalized_type = (document_type or "").strip().lower()
    if normalized_type not in {"certificate", "receipt"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo documento non valido.",
        )

    file_bytes = await file.read()
    url = _upload_to_cloudinary(
        file_bytes=file_bytes,
        filename=file.filename or "documento",
        content_type=file.content_type or "application/octet-stream",
        document_type=normalized_type,
    )

    return {"url": url, "document_type": normalized_type}


@router.post("/", response_model=PublicParentRequestOut)
def create_public_parent_request(
    request_in: PublicParentRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    club_code = request_in.club_code.strip().upper()

    if not request_in.privacy_consent or not request_in.data_processing_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Per inviare la richiesta devi accettare informativa privacy e trattamento dati.",
        )

    club = (
        db.query(Club)
        .filter(Club.public_code == club_code)
        .first()
    )

    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codice società non valido",
        )

    parent_request = ParentRequest(
        club_id=club.id,
        athlete_first_name=request_in.athlete_first_name.strip(),
        athlete_last_name=request_in.athlete_last_name.strip(),
        athlete_birth_date=request_in.athlete_birth_date,
        requested_group=(request_in.requested_group or "").strip() or None,
        parent_name=request_in.parent_name.strip(),
        parent_phone=(request_in.parent_phone or "").strip() or None,
        parent_email=request_in.parent_email.strip(),
        notes=(request_in.notes or "").strip() or None,
        certificate_file_url=(request_in.certificate_file_url or "").strip() or None,
        payment_receipt_url=(request_in.payment_receipt_url or "").strip() or None,
        privacy_consent=request_in.privacy_consent,
        data_processing_consent=request_in.data_processing_consent,
        status="pending",
    )

    db.add(parent_request)
    db.flush()

    create_audit_log(
        db,
        action="parent_request_consent_collected",
        club_id=club.id,
        actor_type="parent",
        target_type="parent_request",
        target_id=parent_request.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={
            "privacy_consent": request_in.privacy_consent,
            "data_processing_consent": request_in.data_processing_consent,
            "parent_email": request_in.parent_email,
        },
    )
    db.commit()
    db.refresh(parent_request)

    return PublicParentRequestOut(
        id=parent_request.id,
        status=parent_request.status,
        club_name=club.name,
        athlete_first_name=parent_request.athlete_first_name,
        athlete_last_name=parent_request.athlete_last_name,
        requested_group=parent_request.requested_group,
        created_at=parent_request.created_at,
    )
