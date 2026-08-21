from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""

    status: str = Field(..., json_schema_extra={"example": "healthy"})
    service: str = Field(..., json_schema_extra={"example": "AgentCart API"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})

