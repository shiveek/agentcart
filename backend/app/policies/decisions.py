from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """Possible outcomes of policy evaluation."""

    ALLOW = "ALLOW"
    ALLOW_WITH_APPROVAL = "ALLOW_WITH_APPROVAL"
    BLOCK = "BLOCK"


class PolicyDecision(BaseModel):
    """Structured result returned by the policy engine."""

    decision: DecisionType
    allowed: bool
    requires_approval: bool
    reasons: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
