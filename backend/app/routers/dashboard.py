from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta

from ..db.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.athlete import Athlete
from ..models.payment import Payment
from ..models.certificate import Certificate
from ..models.parent_request import ParentRequest
from ..models.communication import Communication


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _athlete_name(athlete: Athlete | None) -> str:
    if not athlete:
        return "Atleta"
    return f"{athlete.first_name or ''} {athlete.last_name or ''}".strip() or "Atleta"


def _payment_residual(payment: Payment) -> float:
    return max(0.0, float(payment.amount_due or 0) - float(payment.amount_paid or 0))


def _build_whatsapp_template(kind: str, club_name: str, parent_name: str, athlete_name: str, **values):
    greeting = f"Ciao {parent_name}," if parent_name else "Ciao,"

    if kind == "payment":
        return {
            "type": "Sollecito quota",
            "recipient": parent_name or "Genitore",
            "athlete": athlete_name,
            "message": (
                f"{greeting}\n"
                f"ti contattiamo dalla segreteria di {club_name} per ricordarti che risulta ancora aperto "
                f"un pagamento relativo a {athlete_name}.\n\n"
                f"Importo residuo: {values.get('amount', '0 euro')}\n"
                f"Scadenza: {values.get('due_date', '-')}\n\n"
                "Se hai gia effettuato il pagamento, puoi inviarci la ricevuta rispondendo a questo messaggio.\n\n"
                f"Grazie,\nSegreteria {club_name}"
            ),
        }

    if kind == "certificate":
        return {
            "type": "Promemoria certificato",
            "recipient": parent_name or "Genitore",
            "athlete": athlete_name,
            "message": (
                f"{greeting}\n"
                f"ti ricordiamo che il certificato medico di {athlete_name} risulta da aggiornare.\n\n"
                f"Scadenza: {values.get('expiry_date', '-')}\n\n"
                "Ti chiediamo gentilmente di consegnare o caricare il nuovo certificato appena disponibile.\n\n"
                f"Grazie,\nSegreteria {club_name}"
            ),
        }

    return {
        "type": "Richiesta iscrizione",
        "recipient": parent_name or "Genitore",
        "athlete": athlete_name,
        "message": (
            f"{greeting}\n"
            f"abbiamo ricevuto la richiesta di iscrizione di {athlete_name} per {club_name}.\n\n"
            "La segreteria sta verificando dati e documenti caricati. Ti aggiorneremo appena la pratica sara completata.\n\n"
            f"Grazie,\nSegreteria {club_name}"
        ),
    }


@router.get("/summary")
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Provide a summary of key statistics for the current user's club.

    Returns counts of athletes, outstanding amounts, overdue payments, and
    certificate statuses.
    """
    club_id = current_user.club_id

    # Count athletes
    athletes_count = db.query(Athlete).filter(Athlete.club_id == club_id).count()

    # Aggregate payment data
    payments = db.query(Payment).filter(Payment.club_id == club_id).all()
    total_residuo = 0.0
    quote_scadute = 0
    today = date.today()
    for p in payments:
        residuo = (p.amount_due or 0.0) - (p.amount_paid or 0.0)
        total_residuo += residuo
        if residuo > 0 and p.due_date and p.due_date < today:
            quote_scadute += 1

    # Certificate status counts
    certs = db.query(Certificate).filter(Certificate.club_id == club_id).all()
    certificati_scaduti = 0
    certificati_in_scadenza = 0
    for c in certs:
        if c.expiry_date and c.expiry_date < today:
            certificati_scaduti += 1
        elif c.expiry_date and (c.expiry_date - today).days <= 30:
            certificati_in_scadenza += 1

    richieste_genitori_pendenti = (
        db.query(ParentRequest)
        .filter(ParentRequest.club_id == club_id, ParentRequest.status == "pending")
        .count()
    )

    return {
        "athletes_count": athletes_count,
        "total_residuo": total_residuo,
        "quote_scadute": quote_scadute,
        "certificati_scaduti": certificati_scaduti,
        "certificati_in_scadenza": certificati_in_scadenza,
        "richieste_genitori_pendenti": richieste_genitori_pendenti,
        "notifications": [
            {
                "type": "payments",
                "severity": "warning",
                "message": f"{quote_scadute} quote scadute da sollecitare.",
                "count": quote_scadute,
            },
            {
                "type": "certificates_expired",
                "severity": "danger",
                "message": f"{certificati_scaduti} certificati medici scaduti.",
                "count": certificati_scaduti,
            },
            {
                "type": "certificates_expiring",
                "severity": "warning",
                "message": f"{certificati_in_scadenza} certificati in scadenza entro 30 giorni.",
                "count": certificati_in_scadenza,
            },
            {
                "type": "parent_requests",
                "severity": "info",
                "message": f"{richieste_genitori_pendenti} richieste genitori da verificare.",
                "count": richieste_genitori_pendenti,
            },
        ],
    }


@router.get("/copilot-plan")
def get_copilot_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    club_id = current_user.club_id
    today = date.today()
    next_30 = today + timedelta(days=30)
    club_name = current_user.club.name if current_user.club else "la societa"

    athletes = db.query(Athlete).filter(Athlete.club_id == club_id).all()
    payments = db.query(Payment).filter(Payment.club_id == club_id).all()
    certificates = db.query(Certificate).filter(Certificate.club_id == club_id).all()
    parent_requests = (
        db.query(ParentRequest)
        .filter(ParentRequest.club_id == club_id)
        .order_by(ParentRequest.created_at.desc(), ParentRequest.id.desc())
        .all()
    )
    communications_count = (
        db.query(Communication)
        .filter(Communication.club_id == club_id)
        .count()
    )

    athlete_by_id = {athlete.id: athlete for athlete in athletes}

    pending_requests = [item for item in parent_requests if item.status == "pending"]
    overdue_payments = [
        payment for payment in payments
        if _payment_residual(payment) > 0 and payment.due_date and payment.due_date < today
    ]
    open_payments = [payment for payment in payments if _payment_residual(payment) > 0]
    expired_certificates = [
        cert for cert in certificates
        if cert.expiry_date and cert.expiry_date < today
    ]
    expiring_certificates = [
        cert for cert in certificates
        if cert.expiry_date and today <= cert.expiry_date <= next_30
    ]

    total_residual = sum(_payment_residual(payment) for payment in open_payments)
    overdue_residual = sum(_payment_residual(payment) for payment in overdue_payments)
    total_urgencies = (
        len(pending_requests)
        + len(overdue_payments)
        + len(expired_certificates)
        + len(expiring_certificates)
    )

    health_score = max(0, 100 - (len(pending_requests) * 8) - (len(overdue_payments) * 10) - (len(expired_certificates) * 14) - (len(expiring_certificates) * 4))
    if total_residual > 0:
        health_score = max(0, health_score - min(18, int(total_residual / 100)))

    if health_score >= 85:
        status = "green"
        headline = "Segreteria sotto controllo"
        summary = "Oggi ClubIQ non vede blocchi critici. Puoi lavorare su aggiornamento dati, iscrizioni e comunicazioni preventive."
    elif health_score >= 60:
        status = "yellow"
        headline = "Giornata da gestire con ordine"
        summary = "Ci sono alcune priorita operative: gestiscile in sequenza per evitare accumulo di solleciti e documenti."
    else:
        status = "red"
        headline = "Priorita alta in segreteria"
        summary = "Quote, certificati o richieste richiedono attenzione rapida. Parti dai blocchi che impattano incassi e idoneita."

    action_plan = []

    if pending_requests:
        action_plan.append({
            "priority": "alta",
            "area": "Iscrizioni",
            "title": f"Verifica {len(pending_requests)} richieste genitori",
            "description": "Approva quelle complete e contatta subito le famiglie con documenti mancanti.",
            "cta_label": "Vai alle richieste",
            "cta_anchor": "#parentRequestsSection",
            "estimated_minutes": min(20, max(5, len(pending_requests) * 4)),
        })

    if overdue_payments:
        action_plan.append({
            "priority": "alta",
            "area": "Incassi",
            "title": f"Sollecita {len(overdue_payments)} quote scadute",
            "description": f"Residuo scaduto stimato: {round(overdue_residual, 2)} euro. Prepara messaggi WhatsApp mirati.",
            "cta_label": "Vai ai pagamenti",
            "cta_anchor": "#paymentsSection",
            "estimated_minutes": min(25, max(6, len(overdue_payments) * 3)),
        })

    if expired_certificates:
        action_plan.append({
            "priority": "alta",
            "area": "Certificati",
            "title": f"Blocca {len(expired_certificates)} certificati scaduti",
            "description": "Invia richiesta di rinnovo e segnala alla segreteria quali atleti non sono coperti.",
            "cta_label": "Vai ai certificati",
            "cta_anchor": "#certificatesSection",
            "estimated_minutes": min(20, max(5, len(expired_certificates) * 3)),
        })

    if expiring_certificates:
        action_plan.append({
            "priority": "media",
            "area": "Prevenzione",
            "title": f"Avvisa {len(expiring_certificates)} famiglie prima della scadenza",
            "description": "Un promemoria oggi evita certificati scaduti nelle prossime settimane.",
            "cta_label": "Prepara promemoria",
            "cta_anchor": "#certificatesSection",
            "estimated_minutes": min(15, max(4, len(expiring_certificates) * 2)),
        })

    if not action_plan:
        action_plan.append({
            "priority": "bassa",
            "area": "Crescita",
            "title": "Prepara una comunicazione preventiva",
            "description": "Usa la giornata libera per aggiornare anagrafiche, inviare link iscrizione o fare report al presidente.",
            "cta_label": "Vai alle comunicazioni",
            "cta_anchor": "#quickCommunicationsSection",
            "estimated_minutes": 8,
        })

    message_templates = []

    for payment in overdue_payments[:3]:
        athlete = athlete_by_id.get(payment.athlete_id)
        message_templates.append(
            _build_whatsapp_template(
                "payment",
                club_name,
                getattr(athlete, "parent_name_1", None) or "Genitore",
                _athlete_name(athlete),
                amount=f"{round(_payment_residual(payment), 2)} euro",
                due_date=payment.due_date.isoformat() if payment.due_date else "-",
            )
        )

    for cert in (expired_certificates + expiring_certificates)[:3]:
        athlete = athlete_by_id.get(cert.athlete_id)
        message_templates.append(
            _build_whatsapp_template(
                "certificate",
                club_name,
                getattr(athlete, "parent_name_1", None) or "Genitore",
                _athlete_name(athlete),
                expiry_date=cert.expiry_date.isoformat() if cert.expiry_date else "-",
            )
        )

    for request in pending_requests[:2]:
        athlete_name = f"{request.athlete_first_name or ''} {request.athlete_last_name or ''}".strip() or "l'atleta"
        message_templates.append(
            _build_whatsapp_template(
                "request",
                club_name,
                request.parent_name or "Genitore",
                athlete_name,
            )
        )

    report_cards = [
        {"label": "Atleti", "value": len(athletes), "detail": "anagrafiche attive in societa"},
        {"label": "Residuo", "value": round(total_residual, 2), "detail": "euro ancora da incassare"},
        {"label": "Quote scadute", "value": len(overdue_payments), "detail": "famiglie da sollecitare"},
        {"label": "Certificati critici", "value": len(expired_certificates) + len(expiring_certificates), "detail": "scaduti o in scadenza"},
    ]

    president_report = {
        "title": f"Report presidente - {club_name}",
        "summary": (
            f"{len(athletes)} atleti censiti, {round(total_residual, 2)} euro da incassare, "
            f"{len(overdue_payments)} quote scadute e {len(expired_certificates) + len(expiring_certificates)} certificati critici."
        ),
        "highlights": [
            f"Incasso residuo totale: {round(total_residual, 2)} euro",
            f"Residuo gia scaduto: {round(overdue_residual, 2)} euro",
            f"Richieste genitori pendenti: {len(pending_requests)}",
            f"Comunicazioni registrate: {communications_count}",
        ],
        "risks": [
            item for item in [
                f"{len(overdue_payments)} quote scadute da recuperare" if overdue_payments else None,
                f"{len(expired_certificates)} certificati scaduti" if expired_certificates else None,
                f"{len(pending_requests)} richieste iscrizione in attesa" if pending_requests else None,
            ] if item
        ] or ["Nessun rischio operativo grave rilevato oggi."],
    }

    club = current_user.club
    onboarding_steps = [
        {
            "title": "Completa dati societa",
            "done": bool(getattr(club, "email", None) and getattr(club, "phone", None)),
            "hint": "Email e telefono rendono professionali messaggi, report e link genitori.",
            "anchor": "#clubProfileSection",
        },
        {
            "title": "Carica logo societa",
            "done": bool(getattr(club, "logo", None)),
            "hint": "Il logo rende riconoscibili dashboard e comunicazioni.",
            "anchor": "#clubProfileSection",
        },
        {
            "title": "Attiva link iscrizione genitori",
            "done": bool(getattr(club, "public_code", None)),
            "hint": "Il link pubblico trasforma richieste WhatsApp in pratiche ordinate.",
            "anchor": "#clubRegistrationSection",
        },
        {
            "title": "Importa o crea i primi atleti",
            "done": len(athletes) > 0,
            "hint": "Puoi partire con il CSV se hai gia un elenco Excel.",
            "anchor": "#athleteImportSection",
        },
        {
            "title": "Registra almeno una comunicazione",
            "done": communications_count > 0,
            "hint": "Cosi la societa ha storico reale, non solo messaggi nel telefono.",
            "anchor": "#quickCommunicationsSection",
        },
    ]

    automation_suggestions = [
        {
            "name": "Sollecito quota scaduta",
            "trigger": "Pagamento con residuo e scadenza passata",
            "audience": f"{len(overdue_payments)} famiglie oggi",
            "channel": "WhatsApp",
            "status": "ready" if overdue_payments else "standby",
        },
        {
            "name": "Promemoria certificato",
            "trigger": "Certificato scaduto o in scadenza entro 30 giorni",
            "audience": f"{len(expired_certificates) + len(expiring_certificates)} famiglie oggi",
            "channel": "WhatsApp",
            "status": "ready" if (expired_certificates or expiring_certificates) else "standby",
        },
        {
            "name": "Follow-up iscrizione",
            "trigger": "Richiesta genitore ancora pending",
            "audience": f"{len(pending_requests)} richieste oggi",
            "channel": "WhatsApp",
            "status": "ready" if pending_requests else "standby",
        },
    ]

    message_library = [
        {
            "type": "Benvenuto nuova famiglia",
            "message": (
                f"Ciao, benvenuto in {club_name}. Da oggi useremo ClubIQ per iscrizioni, documenti, quote e comunicazioni importanti."
            ),
        },
        {
            "type": "Documenti mancanti",
            "message": (
                f"Ciao, per completare la pratica con {club_name} manca ancora un documento. Puoi inviarlo qui o caricarlo dal link iscrizione."
            ),
        },
        {
            "type": "Promemoria quota",
            "message": (
                f"Ciao, ti ricordiamo la quota sportiva aperta con {club_name}. Se hai gia pagato, inviaci pure la ricevuta."
            ),
        },
    ]

    differentiators = [
        "ClubIQ non mostra solo dati: suggerisce cosa fare oggi.",
        "WhatsApp-first: ogni priorita puo diventare un messaggio pronto.",
        "Report presidente sintetico: incassi, residui, certificati e richieste in un solo quadro.",
        "Workflow genitore-segreteria: richiesta, documenti, approvazione e atleta creato.",
    ]

    next_best_features = [
        {"feature": "Import CSV atleti", "reason": "Riduce il tempo di onboarding delle societa nuove."},
        {"feature": "Area genitore", "reason": "Sposta documenti e aggiornamenti fuori dalla chat manuale."},
        {"feature": "Automazioni premium", "reason": "Trasforma solleciti e promemoria in valore ricorrente."},
    ]

    return {
        "status": status,
        "health_score": health_score,
        "headline": headline,
        "summary": summary,
        "estimated_minutes": sum(item["estimated_minutes"] for item in action_plan),
        "action_plan": action_plan[:6],
        "message_templates": message_templates[:6],
        "message_library": message_library,
        "report_cards": report_cards,
        "president_report": president_report,
        "onboarding_steps": onboarding_steps,
        "automation_suggestions": automation_suggestions,
        "csv_import": {
            "accepted_format": "CSV UTF-8",
            "required_columns": ["first_name", "last_name", "birth_date"],
            "optional_columns": ["group_name", "phone", "email", "parent_name_1", "parent_phone_1", "parent_email_1", "notes"],
            "example": "first_name,last_name,birth_date,group_name,parent_name_1,parent_phone_1,parent_email_1",
        },
        "differentiators": differentiators,
        "next_best_features": next_best_features,
    }
