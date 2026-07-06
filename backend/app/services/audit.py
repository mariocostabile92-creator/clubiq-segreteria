import json
from typing import Any

from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    *,
    action: str,
    club_id: int | None = None,
    user_id: int | None = None,
    actor_type: str = "system",
    target_type: str | None = None,
    target_id: str | int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    audit = AuditLog(
        club_id=club_id,
        user_id=user_id,
        actor_type=actor_type,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
    )
    db.add(audit)
    return audit
