import json
import os
from urllib import error as urlerror, request as urlrequest


def whatsapp_configured() -> bool:
    return bool(os.getenv("WHATSAPP_ACCESS_TOKEN") and os.getenv("WHATSAPP_PHONE_NUMBER_ID"))


def send_whatsapp_text(to_phone: str, message: str) -> bool:
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()

    if not token or not phone_number_id:
        raise RuntimeError("WhatsApp Cloud API non configurata.")

    clean_phone = "".join(ch for ch in str(to_phone or "") if ch.isdigit())
    if not clean_phone:
        raise RuntimeError("Numero WhatsApp mancante.")

    payload = {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }

    req = urlrequest.Request(
        f"https://graph.facebook.com/v20.0/{phone_number_id}/messages",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            return 200 <= response.status < 300
    except urlerror.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Errore WhatsApp {exc.code}: {body}") from exc
    except urlerror.URLError as exc:
        raise RuntimeError(f"Errore connessione WhatsApp: {exc.reason}") from exc
