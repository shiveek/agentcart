from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services.audit_service import record_audit_event


def test_record_audit_event(db: Session):
    entry = record_audit_event(
        db=db,
        actor_type="USER",
        actor_id="user-123",
        action="test_action",
        resource_type="TestResource",
        resource_id="res-456",
        reason="Testing audit creation",
        metadata={"detail": "sample metadata"},
    )

    assert entry.id is not None
    assert entry.actor_type == "USER"
    assert entry.action == "test_action"

    db_entry = db.query(AuditLog).filter(AuditLog.id == entry.id).first()
    assert db_entry is not None
    assert db_entry.reason == "Testing audit creation"


def test_audit_sanitizes_secrets(db: Session):
    entry = record_audit_event(
        db=db,
        actor_type="USER",
        actor_id="user-789",
        action="user_login",
        resource_type="User",
        metadata={
            "email": "user@test.com",
            "password": "MySuperSecretPassword123!",
            "token": "secret-jwt-token",
        },
    )

    assert entry.metadata_json is not None
    assert "email" in entry.metadata_json
    assert "password" not in entry.metadata_json
    assert "token" not in entry.metadata_json
