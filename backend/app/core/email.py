"""
ClubIQ Segreteria - Email service Brevo
Invio email reale tramite Brevo API senza dipendenze esterne.
"""

import json
import os
import urllib.error
import urllib.request


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def get_email_settings():
    return {
        "api_key": os.getenv("BREVO_API_KEY", "").strip(),
        "from_email": os.getenv("MAIL_FROM_EMAIL", "").strip(),
        "from_name": os.getenv("MAIL_FROM_NAME", "ClubIQ Segreteria").strip(),
        "app_base_url": os.getenv("APP_BASE_URL", "").strip().rstrip("/"),
    }


def is_email_configured() -> bool:
    settings = get_email_settings()
    return bool(settings["api_key"] and settings["from_email"] and settings["app_base_url"])


def send_brevo_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Invia una email tramite Brevo.
    Ritorna True se Brevo accetta la richiesta.
    Solleva RuntimeError con dettaglio chiaro se fallisce.
    """
    settings = get_email_settings()

    if not settings["api_key"]:
        raise RuntimeError("BREVO_API_KEY non configurata.")

    if not settings["from_email"]:
        raise RuntimeError("MAIL_FROM_EMAIL non configurata.")

    if not to_email:
        raise RuntimeError("Destinatario email mancante.")

    payload = {
        "sender": {
            "name": settings["from_name"],
            "email": settings["from_email"],
        },
        "to": [
            {
                "email": to_email,
            }
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        BREVO_API_URL,
        data=data,
        method="POST",
        headers={
            "accept": "application/json",
            "api-key": settings["api_key"],
            "content-type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return 200 <= response.status < 300

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Errore Brevo {exc.code}: {body}") from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(f"Errore connessione Brevo: {exc.reason}") from exc


def build_verify_email_html(verify_link: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#111827;">
        <h2>Verifica la tua email su ClubIQ</h2>
        <p>Per completare la configurazione della tua società, conferma questo indirizzo email.</p>
        <p>
            <a href="{verify_link}" style="display:inline-block;background:#2563eb;color:white;padding:12px 18px;border-radius:10px;text-decoration:none;">
                Verifica email
            </a>
        </p>
        <p>Se il pulsante non funziona, copia e incolla questo link nel browser:</p>
        <p style="word-break:break-all;">{verify_link}</p>
    </div>
    """


def build_reset_password_html(reset_link: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#111827;">
        <h2>Reimposta la password ClubIQ</h2>
        <p>Abbiamo ricevuto una richiesta di reset password per il tuo account.</p>
        <p>
            <a href="{reset_link}" style="display:inline-block;background:#2563eb;color:white;padding:12px 18px;border-radius:10px;text-decoration:none;">
                Reimposta password
            </a>
        </p>
        <p>Se non hai richiesto tu questa operazione, ignora questa email.</p>
        <p>Se il pulsante non funziona, copia e incolla questo link nel browser:</p>
        <p style="word-break:break-all;">{reset_link}</p>
    </div>
    """