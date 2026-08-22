from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Schema for audit log record output."""

    id: UUID
    merchant_id: Optional[UUID] = None
    actor_type: str
    actor_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    reason: Optional[str] = None
    policy_decision: Optional[str] = None
    approval_status: Optional[str] = None
    idempotency_key: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
