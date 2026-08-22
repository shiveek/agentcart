from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def _make_json_safe(obj: Any) -> Any:
    """Recursively convert Decimal, UUID, and other non-JSON types to JSON-serializable objects."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(item) for item in obj]
    return obj


def record_audit_event(
    db: Session,
    actor_type: str,
    action: str,
    resource_type: str,
    merchant_id: Optional[UUID] = None,
    actor_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    reason: Optional[str] = None,
    policy_decision: Optional[str] = None,
    approval_status: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Record a structured audit log event in the database.
    
    Ensures password/token secrets are stripped from metadata before saving.
    """
    safe_metadata = {}
    if metadata:
        for k, v in metadata.items():
            if k.lower() in ("password", "secret", "token", "password_hash", "access_token"):
                continue
            safe_metadata[k] = _make_json_safe(v)

    audit_entry = AuditLog(
        merchant_id=merchant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        reason=reason,
        policy_decision=policy_decision,
        approval_status=approval_status,
        idempotency_key=idempotency_key,
        metadata_json=safe_metadata if safe_metadata else None,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

