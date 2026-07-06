import base64
import hashlib
import json
import os
import time
import uuid
from urllib import parse, request as urlrequest

from fastapi import HTTPException, status


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_UPLOAD_BYTES = 4 * 1024 * 1024


def cloudinary_configured() -> bool:
    return all(
        os.getenv(name, "").strip()
        for name in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
    )


def validate_image_upload(content_type: str | None, file_size: int) -> None:
    if (content_type or "") not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato immagine non supportato. Usa JPG, PNG o WEBP.",
        )

    if file_size > MAX_IMAGE_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Immagine troppo grande. Carica un file massimo da 4 MB.",
        )


def build_image_data_url(content: bytes, content_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def upload_image_to_cloudinary(
    content: bytes,
    filename: str,
    content_type: str,
    folder: str,
) -> str:
    validate_image_upload(content_type, len(content))

    if not cloudinary_configured():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage immagini non configurato. Mancano variabili Cloudinary.",
        )

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()

    timestamp = str(int(time.time()))
    safe_name = "".join(
        ch for ch in (filename or "immagine").rsplit(".", 1)[0]
        if ch.isalnum() or ch in ("-", "_")
    ) or "immagine"
    public_id = f"{folder.strip('/')}/{uuid.uuid4().hex}_{safe_name}"
    params_to_sign = f"folder={folder.strip('/')}&public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()

    data_uri = f"data:{content_type};base64,{base64.b64encode(content).decode('utf-8')}"
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    payload = parse.urlencode({
        "file": data_uri,
        "api_key": api_key,
        "timestamp": timestamp,
        "signature": signature,
        "folder": folder.strip("/"),
        "public_id": public_id,
    }).encode("utf-8")

    req = urlrequest.Request(upload_url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Errore durante il caricamento immagine.",
        ) from exc

    secure_url = result.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upload immagine completato senza URL.",
        )

    return secure_url
