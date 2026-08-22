import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Schema for incoming AI Commerce Agent chat/action requests."""

    merchant_id: uuid.UUID = Field(..., description="ID of the merchant catalog/store")
    customer_identifier: str = Field(
        default="demo-buyer-001", description="Identifier of the AI buyer or end customer"
    )
    message: str = Field(
        ..., description="Natural language prompt or directive for the commerce agent"
    )
    cart_id: Optional[uuid.UUID] = Field(
        default=None, description="Active cart ID if continuing an ongoing session"
    )


class ToolCallTrace(BaseModel):
    """Trace object documenting an autonomous tool call made by the LLM agent."""

    tool_name: str
    arguments: Dict[str, Any]
    output: Any


class AgentChatResponse(BaseModel):
    """Schema for AI Commerce Agent execution response."""

    reply: str = Field(..., description="Final natural language response from the AI Agent")
    cart_id: Optional[uuid.UUID] = Field(default=None, description="Active cart ID")
    order_id: Optional[uuid.UUID] = Field(default=None, description="Order ID if checkout occurred")
    tool_calls: List[ToolCallTrace] = Field(
        default_factory=list, description="Trace of structured tools invoked during reasoning"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
