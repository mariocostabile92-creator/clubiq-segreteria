import os
import requests


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def get_app_base_url() -> str:
    return os.getenv("APP_BASE_URL", "").rstrip("/")


def send_brevo_email(to_email: str, subject: str, html_content: str) -> None:
    api_key = os.getenv("BREVO_API_KEY")
    from_email = os.getenv("MAIL_FROM_EMAIL")
    from_name = os.getenv("MAIL_FROM_NAME", "ClubIQ Segreteria")

    if not api_key or not from_email:
        raise RuntimeError("Configurazione email mancante: BREVO_API_KEY o MAIL_FROM_EMAIL non impostati.")

    payload = {
        "sender": {"name": from_name, "email": from_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    response = requests.post(
        BREVO_API_URL,
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        json=payload,
        timeout=15,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Invio email non riuscito: {response.status_code} {response.text}")


def build_verify_email_html(verify_link: str) -> str:
    return f"""
    <h2>Conferma la tua email ClubIQ</h2>
    <p>Grazie per aver creato la tua società su ClubIQ Segreteria.</p>
    <p>Clicca sul pulsante qui sotto per verificare la tua email.</p>
    <p><a href=\"{verify_link}\" style=\"display:inline-block;padding:12px 18px;background:#0f172a;color:#ffffff;text-decoration:none;border-radius:10px;\">Verifica email</a></p>
    <p>Se il pulsante non funziona, copia questo link nel browser:</p>
    <p>{verify_link}</p>
    """


def build_reset_password_html(reset_link: str) -> str:
    return f"""
    <h2>Reimposta la password ClubIQ</h2>
    <p>Abbiamo ricevuto una richiesta di reset password per il tuo account.</p>
    <p>Clicca sul pulsante qui sotto per impostare una nuova password.</p>
    <p><a href=\"{reset_link}\" style=\"display:inline-block;padding:12px 18px;background:#0f172a;color:#ffffff;text-decoration:none;border-radius:10px;\">Reimposta password</a></p>
    <p>Il link scade tra 60 minuti. Se non hai richiesto tu il reset, ignora questa email.</p>
    <p>{reset_link}</p>
    """
